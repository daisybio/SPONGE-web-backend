#!/usr/bin/env Rscript

packages <- c("SPONGE", "doParallel", "foreach", "dplyr", "randomForest", "argparser", "jsonlite", "ggplot2", "GSVA")
load_packages <- sapply(packages, function(p) {
  suppressWarnings(suppressPackageStartupMessages(library(p, character.only = T)))
})

set.seed(12345)

args.effects = commandArgs(trailingOnly = T)

parser <- arg_parser("Argument parser for spongEffects module", name = "spongEffects_parser")
parser <- add_argument(parser, "--expr", help = "Uploaded gene/transcript expression")
parser <- add_argument(parser, "--model_path", help = "Path to spongEffects models RDS object")

parser <- add_argument(parser, "--output", help = "Output filename", default = "predictions.json")
parser <- add_argument(parser, "--log", help = "Log given expression", flag = T)
parser <- add_argument(parser, "--pseudo_count", help = "Pseudo count", default = 1e-3)
parser <- add_argument(parser, "--subtypes", help = "Predict on subtype level", flag = T)
########################
##  PARAMETER TUNING  ##
########################
parser <- add_argument(parser, "--cpus", help = "Number of cores to use for backend", default = 4)
parser <- add_argument(parser, "--mscor", help = "Mscor threshold", default = 0)
parser <- add_argument(parser, "--fdr", help = "False discovery rate for padj ceRNA interactions", default = 0.05)
parser <- add_argument(parser, "--bin_size", help = "Total bin size for enrichment", default = 100)
parser <- add_argument(parser, "--min_size", help = "Minimum size for enrichment", default = 100)
parser <- add_argument(parser, "--max_size", help = "Maximum size for enrichment", default = 2000)
parser <- add_argument(parser, "--min_expr", help = "Minimum expression for enrichment", default = 10)
parser <- add_argument(parser, "--method", help = "Method", default = "gsva")
parser <- add_argument(parser, "--enrichment_cores", help = "Number of cores to use for enrichment", default = 25)
parser <- add_argument(parser, "--local", help = "No parallel background", flag = T)
# parse arguments
argv_predict <- parse_args(parser, argv = args.effects)
#---------------------------GLOBAL VARIABLES------------------------------------
SUBTYPE_PROJECTS <- c("breast invasive carcinoma", "cervical & endocervical cancer",
                      "esophageal carcinoma", "head & neck squamous cell carcinoma",
                      "brain lower grade glioma", "sarcoma", "stomach adenocarcinoma",
                      "testicular germ cell tumor", "uterine corpus endometrioid carcinoma")

DELIMS <- c(" ", "\t", ",", ";")

#---------------------------FUNCTIONS-------------------------------------------

predict_subtype <- function(df, all_models, test_modules, threshold) {
  type <- as.character(unique(df$typePrediction))
  if (type %in% SUBTYPE_PROJECTS && nrow(df) >= threshold) {
    # get sub samples
    test_modules <- test_modules[,df$sampleID]
    message(Sys.time(), " - predicting subtypes for ", type)

    # match types in model
    type <- gsub("&", "and", gsub(" ", "_", type))

    # get specific model
    model <- all_models[[type]]$model$Model

    # get common modules
    common_modules <- intersect(model$coefnames, rownames(test_modules))
    message(Sys.time(), " - found ", length(common_modules), " common modules", common_modules)
    if (length(common_modules) > 0) {
      test_modules <- test_modules[common_modules,,drop=F]
    } else {
      test_modules <- test_modules[0,,drop=F]
      df$subtypePrediction <- NA
      return(df)
    }

    # fill missing modules if needed
    missing_modules <- setdiff(model$coefnames, rownames(test_modules))
    message(Sys.time(), " - found ", length(missing_modules), " missing modules")
    if (length(missing_modules) > 0) {
      median_value <- median(apply(test_modules, 2, median))
      frac <- 100
      sd <- (max(test_modules) - min(test_modules)) / frac
      test_modules[missing_modules,] <- rnorm(length(missing_modules)*ncol(test_modules), mean = median_value, sd = sd)
    }
    # build input
    Input.test <- t(test_modules) %>% scale(center = T, scale = T)
    df$subtypePrediction <- as.vector(predict(model, Input.test))
    return(df)
  } else {
    df$subtypePrediction <- NA
    return(df)
  }
}

determine_delimiter <- function(path) {
  delim_test <- readLines(path, n = 1)
  test <- sapply(DELIMS, function(d) length(strsplit(delim_test, d)[[1]]))
  names(which(test == max(test)))
}

read_expr <- function(path) {
  delim <- determine_delimiter(path)
  expr <- read.csv(path, sep = delim, check.names = F)
  cols_test <- all(grepl("ENS", colnames(expr)))
  rows_test <- all(grepl("ENS", rownames(expr)))
  id_col_test <- apply(expr[2,], 2, function(col) all(grepl("ENS", col)))
  # ID column detected
  if (any(id_col_test)){
    expr <- data.frame(expr, row.names = colnames(expr)[id_col_test], check.names = F) %>%
      as.matrix()
    # columns are IDs
  } else if (cols_test)  {
    expr <- expr %>% t()
  } else if (rows_test) {
    expr <- expr %>% as.matrix()
  } else {
    stop("Expression file has to contain ensembl IDs in either row names, colum names, or a data column")
  }
  # rows are IDs and expression can be used as it is
  return(expr)
}
#---------------------------PARAMETERS------------------------------------------
startTime <- Sys.time()
message(startTime, " - STARTING EXECUTION:")
#---------------------------READ UPLOADED EXPRESSION----------------------------
test_expr <- read_expr(argv_predict$expr)
if(argv_predict$log) {
  test_expr <- log2(test_expr+argv_predict$pseudo_count)
}

# determine level
level_test <- rownames(test_expr)[1]
if(grepl("ENSG", level_test)) {
  level <- "gene"
} else if (grepl("ENST", level_test)) {
  level <- "transcript"
} else {
  stop("Please provide either ensembl gene or transcript IDs in the expression")
}
message(Sys.time(), " - using ", level, " level")

#---------------------------PREPARE EXPRESSION----------------------------------
# uploaded expression samples
samples <- colnames(test_expr)
#---------------------------LOAD MODElS-----------------------------------------
message(Sys.time(), " - Loading spongEffects models")
models <- readRDS(argv_predict$model_path)
# select level
models <- models[[level]]
Sponge.modules <- models$expression_across_types$modules

#---------------------------CALCULATE MODULES-----------------------------------
if (!argv_predict$local) {
  message("registering back end with ", argv_predict$enrichment_cores, " cores\n")
  cl <- makeCluster(argv_predict$enrichment_cores)
  registerDoParallel(cl)
} else {
  message(Sys.time(), " - running on single core")
}
message(Sys.time(), " - enriching type modules (test)")
test.modules.uploaded <-  enrichment_modules(Expr.matrix = test_expr,
                                             modules = Sponge.modules,
                                             bin.size = argv_predict$bin_size,
                                             min.size = argv_predict$min_size,
                                             max.size = argv_predict$max_size,
                                             min.expr = argv_predict$min_expr,
                                             method = argv_predict$method,
                                             cores = argv_predict$enrichment_cores)
message(Sys.time(), " - finished enriching type modules (test)")
#--------------------------PREDICT CANCER TYPE----------------------------------
#---------------------------LOAD MODEL------------------------------------------
message(Sys.time(), " - Loading pancan model")
trained.model <- models$expression_across_types$model
# filter for common modules in test and train
common_modules <- intersect(trained.model$Model$coefnames, rownames(test.modules.uploaded))
test.modules.uploaded.pancan <- test.modules.uploaded[common_modules, ]

# fill missing modules if needed
missing_modules <- setdiff(trained.model$Model$coefnames, rownames(test.modules.uploaded))
if (length(missing_modules) > 0) {
  median_value <- median(apply(test.modules.uploaded, 2, median))
  frac <- 100
  sd <- (max(test.modules.uploaded) - min(test.modules.uploaded)) / frac
  test.modules.uploaded.pancan[missing_modules,] <- rnorm(length(missing_modules)*ncol(test.modules.uploaded), mean = median_value, sd = sd)
}
# transform new input data
Input.test.pancan <- t(test.modules.uploaded.pancan) %>% scale(center = T, scale = T)
# predict
type_predictions <- predict(trained.model$Model, Input.test.pancan)
# build table with results
predictions <- data.frame(sampleID=samples, typePrediction=type_predictions, subtypePrediction=NA)


#-----------------PREDICT SUB-TYPES FOR TYPE PREDICTIONS------------------------
if (argv_predict$subtypes) {
  type_splits <- split(predictions, as.vector(predictions$typePrediction))

  # predict subtypes for samples with matching type classification
  predictions <- do.call(rbind, lapply(type_splits,
                                       predict_subtype,
                                       models, test.modules.uploaded, 2))
}
# clean up resources
if (!argv_predict$local) {
  stopCluster(cl)
}
# determine runtime
endTime <- Sys.time()
runTime <- as.double(difftime(endTime, startTime, units = c("secs")))
# determine dominant predictions
type_predictions_table <- table(predictions$typePrediction)
dominant_type <- names(type_predictions_table)[max(type_predictions_table)==type_predictions_table]
dominant_subtype <- NA
if (argv_predict$subtypes) {
  subtype_predictions_table <- table(predictions$subtypePrediction)
  dominant_subtype <- names(subtype_predictions_table)[max(subtype_predictions_table)==subtype_predictions_table]
}

# build supplementary information
meta <- data.frame(runtime=runTime, level=level, n_samples=nrow(predictions),
                   type_predict=dominant_type, subtype_predict=dominant_subtype, script_version="0.1.1")

# return as JSON for API processing
responseObj <- list(meta=meta, data=predictions)
message(Sys.time(), " - FINISHED EXECUTION")
message("Writing output file to ", argv_predict$output)
write_json(responseObj, path = argv_predict$output)
