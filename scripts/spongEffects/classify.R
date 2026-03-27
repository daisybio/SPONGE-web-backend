#!/usr/bin/env Rscript
packages <- c("SPONGE", "doParallel", "foreach", "dplyr", "randomForest", "argparser", "jsonlite", "ggplot2", "GSVA")
load_packages <- sapply(packages, function(p) {
  suppressWarnings(suppressPackageStartupMessages(library(p, character.only = T)))
})
set.seed(12345)

args.effects <- commandArgs(trailingOnly = T)

parser <- arg_parser("Argument parser for spongEffects module", name = "spongEffects_parser")
parser <- add_argument(parser, "--expr", help = "Uploaded gene/transcript expression")
parser <- add_argument(parser, "--model_path", help = "Path to spongEffects models RDS object")

parser <- add_argument(parser, "--output", help = "Output filename", default = "predictions.json")
parser <- add_argument(parser, "--log", help = "Log given expression", flag = T)
parser <- add_argument(parser, "--pseudo_count", help = "Pseudo count", default = 1e-3)
parser <- add_argument(parser, "--subtypes", help = "Predict on subtype level", flag = T)
parser <- add_argument(parser, "--model", help = "Model to use: One specific cancer type.
If None (old behaviour): first pancancer is used to predict the type for each sample,
then for each sample the predicted type model is used. (if subtype=True)", default = "None")
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

# dev:
# argv_predict$model_path <- "/Users/lena/Projects/SPONGE/SPONGE-web-backend/models.RDS"
# argv_predict$expr <- "/Users/lena/Projects/SPONGE/SPONGE-web-backend/uploads/GSE123845_exp_tpm_matrix_processed.csv"
# argv_predict$model <- "breast_invasive_carcinoma"
# argv_predict$log <- T

# setup logging to file
log_file <- sub("\\.json$", ".log", argv_predict$output)
log_con <- file(log_file, open = "wt")
sink(log_con, type = "output")
sink(log_con, type = "message")

sessionInfo()
print(getwd())

# write args to log file, pretty
print(argv_predict)

#---------------------------GLOBAL VARIABLES------------------------------------
SUBTYPE_PROJECTS <- c(
  "breast invasive carcinoma", "cervical & endocervical cancer",
  "esophageal carcinoma", "head & neck squamous cell carcinoma",
  "brain lower grade glioma", "sarcoma", "stomach adenocarcinoma",
  "testicular germ cell tumor", "uterine corpus endometrioid carcinoma"
)

SAMPLES_THRESHOLD <- 2

DELIMS <- c(" ", "\t", ",", ";")

#---------------------------FUNCTIONS-------------------------------------------

predict_subtype <- function(type, sample_list, all_models, test_modules, threshold) {
  # type <- as.character(unique(df$typePrediction))
  type_project_style <- gsub("and", "&", gsub("_", " ", type))
  type <- gsub("&", "and", gsub(" ", "_", type))
  if (type_project_style %in% SUBTYPE_PROJECTS && length(sample_list) >= threshold) {
    # get sub samples
    # test_modules <- test_modules[,df$sampleID]
    message(Sys.time(), " - predicting subtypes for ", type)

    # match types in model
    type <- gsub("&", "and", gsub(" ", "_", type))

    # get specific model
    model <- all_models[[type]]$model$Model

    # get common modules
    common_modules <- intersect(model$coefnames, rownames(test_modules))
    message(Sys.time(), " - found ", length(common_modules), " common modules", common_modules)
    if (length(common_modules) > 0) {
      test_modules <- test_modules[common_modules, , drop = F]
    } else {
      test_modules <- test_modules[0, , drop = F]
      subtypePrediction <- NA
      return(subtypePrediction)
    }

    # fill missing modules if needed
    missing_modules <- setdiff(model$coefnames, rownames(test_modules))
    message(Sys.time(), " - found ", length(missing_modules), " missing modules")
    if (length(missing_modules) > 0) {
      median_value <- median(apply(test_modules, 2, median))
      frac <- 100
      sd <- (max(test_modules) - min(test_modules)) / frac
      test_modules[missing_modules, ] <- rnorm(length(missing_modules) * ncol(test_modules), mean = median_value, sd = sd)
    }
    # build input
    Input.test <- t(test_modules) %>% scale(center = T, scale = T)
    subtypePrediction <- as.vector(predict(model, Input.test))
    return(subtypePrediction)
  } else {
    subtypePrediction <- NA
    return(subtypePrediction)
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
  id_col_test <- apply(expr[2, ], 2, function(col) all(grepl("ENS", col)))
  # ID column detected
  if (any(id_col_test)) {
    expr <- data.frame(expr, row.names = colnames(expr)[id_col_test], check.names = F) %>%
      as.matrix()
    # columns are IDs
  } else if (cols_test) {
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
if (argv_predict$log) {
  test_expr <- log2(test_expr + argv_predict$pseudo_count)
}

# determine level
level_test <- rownames(test_expr)[1]
if (grepl("ENSG", level_test)) {
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

#---------------------------REGISTER PARALLEL-----------------------------------
if (!argv_predict$local) {
  message("registering back end with ", argv_predict$enrichment_cores, " cores\n")
  cl <- makeCluster(argv_predict$enrichment_cores)
  registerDoParallel(cl)
} else {
  message(Sys.time(), " - running on single core")
}

#---------------------------CALCULATE MODULES-----------------------------------

message(Sys.time(), " - enriching type modules (pancancer)")
Sponge.modules <- models$expression_across_types$modules
test.modules.uploaded <- enrichment_modules(
  Expr.matrix = test_expr,
  modules = Sponge.modules,
  bin.size = argv_predict$bin_size,
  min.size = argv_predict$min_size,
  max.size = argv_predict$max_size,
  min.expr = argv_predict$min_expr,
  method = argv_predict$method,
  cores = argv_predict$enrichment_cores
)

# write.table(test.modules.uploaded, file = "test_modules.tsv", sep = "\t", quote = F)
message(Sys.time(), " - finished enriching type modules (pancancer)")

if (is.null(argv_predict$model) || argv_predict$model == "None" || argv_predict$model == "pancancer" || argv_predict$model == "Pancancer") {
  #--------------------------PREDICT CANCER TYPE----------------------------------
  #---------------------------LOAD MODEL------------------------------------------
  message(Sys.time(), " - Loading pancan model")
  trained.model <- models$expression_across_types$model
  # filter for common modules in test and train
  common_modules <- intersect(trained.model$Model$coefnames, rownames(test.modules.uploaded))
  message(Sys.time(), " - modules in train: ", length(trained.model$Model$coefnames), " and in test: ", length(rownames(test.modules.uploaded)))
  message(Sys.time(), " - found ", length(common_modules), " common modules")
  # message(Sys.time(), " - train modules: ", paste(trained.model$Model$coefnames, collapse = ", "))
  # message(Sys.time(), " - test modules: ", paste(rownames(test.modules.uploaded), collapse = ", "))
  test.modules.uploaded.pancan <- test.modules.uploaded[common_modules, ]
  message(Sys.time(), " Sponge.modules :", length(Sponge.modules))

  # fill missing modules if needed
  missing_modules <- setdiff(trained.model$Model$coefnames, rownames(test.modules.uploaded))
  message(Sys.time(), " - found ", length(missing_modules), " missing modules")
  if (length(missing_modules) > 0) {
    median_value <- median(apply(test.modules.uploaded, 2, median))
    frac <- 100
    sd <- (max(test.modules.uploaded) - min(test.modules.uploaded)) / frac
    test.modules.uploaded.pancan[missing_modules, ] <- rnorm(length(missing_modules) * ncol(test.modules.uploaded), mean = median_value, sd = sd)
  }
  # transform new input data
  Input.test.pancan <- t(test.modules.uploaded.pancan) %>% scale(center = T, scale = T)
  # predict
  type_predictions <- predict(trained.model$Model, Input.test.pancan)
  # build table with results
  predictions <- data.frame(sampleID = samples, typePrediction = type_predictions, subtypePrediction = NA)


  #-----------------PREDICT SUB-TYPES FOR TYPE PREDICTIONS------------------------
  if (argv_predict$subtypes) {
    type_splits <- split(predictions, as.vector(predictions$typePrediction))

    message(Sys.time(), " - predicting subtypes for each type prediction")
    message("type_splits heads: ", head(type_splits))
    message("type_splits: ", type_splits)

    # for each split, compute the enrichment scores: use all samples for which the type was predicted
    test.modules.updated.types <- lapply(names(type_splits), function(type) {
      # match types in model
      type_renamed <- gsub("&", "and", gsub(" ", "_", type))
      x <- type_splits[[type]]
      if (!type_renamed %in% names(models)) {
        message("type not in models: ", type)
        return(NULL)
      } else {
        message("running enrichment for type: ", type)
      }

      type_expression <- test_expr[, x$sampleID, drop = FALSE]
      message("n samples for type ", type, ": ", dim(type_expression)[2])

      type_modules <- models[[type_renamed]]$modules
      message("n modules for type ", type, ": ", length(type_modules))

      tryCatch(
        {
          test.modules.updated <- enrichment_modules(
            Expr.matrix = type_expression,
            modules = type_modules,
            bin.size = argv_predict$bin_size,
            min.size = argv_predict$min_size,
            max.size = argv_predict$max_size,
            min.expr = argv_predict$min_expr,
            method = argv_predict$method,
            cores = argv_predict$enrichment_cores
          )
          # do hierarchical clustering on enrichment scores on genes and samples
          row_order <- hclust(dist(test.modules.updated, method = "euclidean"), method = "ward.D2")$order
          col_order <- hclust(dist(t(test.modules.updated), method = "euclidean"), method = "ward.D2")$order
          test.modules.updated <- test.modules.updated[row_order, col_order]
          message("returning enrichment scores for type: ", type, " with n modules: ", dim(test.modules.updated)[1])
          return(test.modules.updated)
        },
        error = function(e) {
          message("Error enriching type ", type, ": ", e$message)
          return(NULL)
        }
      )
    })
    names(test.modules.updated.types) <- names(type_splits)

    # predict subtypes for samples with matching type classification
    predictions <- do.call(rbind, lapply(names(type_splits), function(type) {
      df <- type_splits[[type]]
      type_clean <- gsub("&", "and", gsub(" ", "_", type))
      samples <- df$sampleID
      modules <- test.modules.updated.types[[type]][, samples, drop = FALSE]
      subtypePrediction <- predict_subtype(
        type = type_clean,
        sample_list = samples,
        all_models = models,
        test_modules = modules,
        threshold = SAMPLES_THRESHOLD
      )
      df$subtypePrediction <- subtypePrediction
      return(df)
    }))
    subtype_predictions_table <- table(predictions$subtypePrediction)
    dominant_subtype <- names(subtype_predictions_table)[max(subtype_predictions_table) == subtype_predictions_table]
  } else {
    dominant_subtype <- NA
  }

  # determine dominant predictions
  type_predictions_table <- table(predictions$typePrediction)
  dominant_type <- names(type_predictions_table)[max(type_predictions_table) == type_predictions_table]
} else {
  #---------------------------ONLY SPECIFIED MODEL----------------------------------
  # if model type is already known:
  # - still do enrichment on pancancer (above, before if)
  # - don't do prediction on pancander
  # if additionally subtype is true
  # - do both enrichment and subtype prediction only on specified type

  model_name <- argv_predict$model
  model_name <- gsub("&", "and", gsub(" ", "_", model_name))
  message(Sys.time(), " - selecting model: ", model_name)
  model <- models[[model_name]]$model$Model
  modules <- models[[model_name]]$modules
  samples <- colnames(test_expr)
  predictions <- data.frame(sampleID = samples, typePrediction = NA, subtypePrediction = NA)

  # do enrichment only on specified type
  message(Sys.time(), " - enriching type modules (test)")
  test.modules.uploaded.type <- enrichment_modules(
    Expr.matrix = test_expr,
    modules = modules,
    bin.size = argv_predict$bin_size,
    min.size = argv_predict$min_size,
    max.size = argv_predict$max_size,
    min.expr = argv_predict$min_expr,
    method = argv_predict$method,
    cores = argv_predict$enrichment_cores
  )

  # do hierarchical clustering on enrichment scores on genes and samples
  row_order <- hclust(dist(test.modules.uploaded.type, method = "euclidean"), method = "ward.D2")$order
  col_order <- hclust(dist(t(test.modules.uploaded.type), method = "euclidean"), method = "ward.D2")$order
  test.modules.uploaded.type <- test.modules.uploaded.type[row_order, col_order]

  # do subtype prediction only on specified type
  if (argv_predict$subtypes) {
    message(Sys.time(), " - predicting subtype")
    subtypePrediction <- predict_subtype(
      type = model_name,
      sample_list = samples,
      all_models = models,
      test_modules = test.modules.uploaded,
      threshold = SAMPLES_THRESHOLD
    )
    predictions$subtypePrediction <- subtypePrediction

    subtype_predictions_table <- table(subtypePrediction)
    dominant_subtype <- names(subtype_predictions_table)[max(subtype_predictions_table) == subtype_predictions_table]
  } else {
    dominant_subtype <- NULL
  }
  dominant_type <- NULL
}

#-----------------WRAPPING UP------------------------

# clean up resources
if (!argv_predict$local) {
  message(Sys.time(), " - Cleaning up resources")
  stopCluster(cl)
}
# determine runtime
endTime <- Sys.time()
runTime <- as.double(difftime(endTime, startTime, units = c("secs")))

# build supplementary information
meta <- data.frame(
  runtime = runTime, level = level, n_samples = ncol(test_expr),
  type_predict = if (is.null(dominant_type)) "NA" else dominant_type,
  subtype_predict = if (is.null(dominant_subtype)) "NA" else dominant_subtype,
  specified_type = argv_predict$model,
  script_version = "0.1.3"
) # see changelog at the bottom

# return as JSON for API processing
scores_df <- as.data.frame(test.modules.uploaded)
scores_list <- list(
  samples = colnames(scores_df),
  genes = rownames(scores_df),
  values = lapply(1:nrow(scores_df), function(i) {
    as.numeric(scores_df[i, ])
  })
)
# append type-specific scores
if (argv_predict$subtypes) {
  if (!is.null(argv_predict$model) && argv_predict$model != "None") {
    type_scores <- list(
      samples = colnames(test.modules.uploaded.type),
      genes = rownames(test.modules.uploaded.type),
      values = lapply(seq_len(nrow(test.modules.uploaded.type)), function(i) {
        as.numeric(test.modules.uploaded.type[i, ])
      })
    )
    type_scores <- setNames(list(type_scores), argv_predict$model)
  } else {
    type_scores <- lapply(names(type_splits), function(type) {
      df_type <- as.data.frame(test.modules.updated.types[[type]])
      list(
        samples = colnames(df_type),
        genes = rownames(df_type), # actually modules
        values = lapply(seq_len(nrow(df_type)), function(i) {
          as.numeric(df_type[i, ])
        })
      )
    })
    names(type_scores) <- names(type_splits)
  }
} else {
  type_scores <- NULL
}

responseObj <- list(meta = meta, data = predictions, scores = scores_list, type_scores = type_scores)

message(Sys.time(), " - FINISHED EXECUTION")
message("Writing output file to ", argv_predict$output)
write_json(responseObj, path = argv_predict$output)

################################################################################
##                                 Changelog                                  ##
################################################################################


# 0.1.3 (Lena)
# - added parameter --model to select a specific model: If this is set,
# - still do enrichment on pancancer
# - don't do prediction on pancander
# - do both enrichment and subtype prediction only on specified type
# -> uploads/example_prediction_model_BRCA.json

# 0.1.2 (Lena)
# - recompute enrichment scores for each type instead of reusing pancancer.
#   pancancer-enrichment scores for type prediction. They are also returned:
#   type_scores
# - log messages are written to a file
# -> uploads/example_prediction.json

# 0.1.1 (Lena)
# returning also enrichment scores

# earlier: Leon?
