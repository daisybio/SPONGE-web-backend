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

# minimum fraction of a model's features (coefnames) that must be present in the enriched test
# matrix; below this the missing features would be mostly noise-filled, so no label is returned
COVERAGE_THRESHOLD <- 0.5

DELIMS <- c(" ", "\t", ",", ";")

# per-model feature coverage, filled by record_coverage() and reported in meta
module_coverage <- list()

#---------------------------FUNCTIONS-------------------------------------------

# Log and record how many of a model's features the test matrix provides.
# Returns TRUE if coverage is sufficient to trust the model's prediction.
record_coverage <- function(model_key, coefnames, test_modules) {
  matched <- length(intersect(coefnames, rownames(test_modules)))
  expected <- length(coefnames)
  fraction <- if (expected > 0) matched / expected else 0
  message(Sys.time(), " - module coverage for ", model_key, ": ", matched, "/", expected, " (", round(fraction, 3), ")")
  module_coverage[[model_key]] <<- data.frame(
    model = model_key, modules_matched = matched, modules_expected = expected,
    coverage = round(fraction, 4), low_coverage = fraction < COVERAGE_THRESHOLD
  )
  if (fraction < COVERAGE_THRESHOLD) {
    message(Sys.time(), " - WARNING: coverage for ", model_key, " below ", COVERAGE_THRESHOLD, ", not returning a prediction")
  }
  fraction >= COVERAGE_THRESHOLD
}

# enrichment_modules() returns NULL when nothing could be scored and a printed string for an
# unknown method; stop here so the cause reaches the API error instead of a later NA comparison.
check_enrichment <- function(enriched, module_set) {
  if (!(is.data.frame(enriched) || is.matrix(enriched)) || nrow(enriched) == 0) {
    stop(
      "Enrichment with method '", argv_predict$method, "' returned no module scores for module set '", module_set,
      "' (method must be one of OE, gsva, ssgsea; check min_size=", argv_predict$min_size, ", max_size=", argv_predict$max_size,
      ", min_expr=", argv_predict$min_expr, " against the module sizes and the uploaded IDs)"
    )
  }
  enriched
}

predict_subtype <- function(type, sample_list, all_models, test_modules, threshold) { # nolint: line_length_linter.
  # type <- as.character(unique(df$typePrediction)) # nolint: commented_code_linter.
  type_project_style <- gsub("and", "&", gsub("_", " ", type))
  type <- gsub("&", "and", gsub(" ", "_", type))
  if (type_project_style %in% SUBTYPE_PROJECTS && length(sample_list) >= threshold) {
    # get sub samples
    # test_modules <- test_modules[,df$sampleID]
    message(Sys.time(), " - predicting subtypes for type: ", type)
    message(Sys.time(), " - number of samples for subtype prediction: ", length(sample_list))

    # match types in model
    type <- gsub("&", "and", gsub(" ", "_", type))
    message(Sys.time(), " - using model key: ", type)

    # get specific model
    if (!type %in% names(all_models)) {
      message(Sys.time(), " - WARNING: model for ", type, " not found in all_models")
      subtypePrediction <- NA
      return(subtypePrediction)
    }
    model <- all_models[[type]]$model$Model

    # get common modules
    common_modules <- intersect(model$coefnames, rownames(test_modules))
    message(Sys.time(), " - modules in model: ", length(model$coefnames))
    message(Sys.time(), " - modules in test: ", length(rownames(test_modules)))
    message(Sys.time(), " - found ", length(common_modules), " common modules")
    if (!record_coverage(type, model$coefnames, test_modules)) {
      subtypePrediction <- NA
      return(subtypePrediction)
    }
    test_modules <- test_modules[common_modules, , drop = F]

    # fill missing modules if needed (coverage is >= COVERAGE_THRESHOLD here)
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
message(Sys.time(), " - expression matrix loaded with ", nrow(test_expr), " rows and ", ncol(test_expr), " columns")

if (argv_predict$log) {
  message(Sys.time(), " - applying log2 transformation (pseudo-count: ", argv_predict$pseudo_count, ")")
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
message(Sys.time(), " - Loading spongEffects models from: ", argv_predict$model_path)
models_raw <- readRDS(argv_predict$model_path)
message(Sys.time(), " - available levels in RDS: ", paste(names(models_raw), collapse = ", "))

# select level
if (!level %in% names(models_raw)) {
  stop("Level '", level, "' not found in models RDS")
}
models <- models_raw[[level]]
message(Sys.time(), " - number of projects in ", level, " level: ", length(names(models)))

#---------------------------REGISTER PARALLEL-----------------------------------
if (!argv_predict$local) {
  message(Sys.time(), " - registering back end with ", argv_predict$enrichment_cores, " cores")
  cl <- makeCluster(argv_predict$enrichment_cores)
  registerDoParallel(cl)
} else {
  message(Sys.time(), " - running on single core")
}

#---------------------------CALCULATE MODULES-----------------------------------

message(Sys.time(), " - enriching type modules (pancancer)")
Sponge.modules <- models$expression_across_types$modules
message(Sys.time(), " - number of modules to enrich: ", length(Sponge.modules))
message(Sys.time(), " - enrichment parameters: method=", argv_predict$method, ", bin_size=", argv_predict$bin_size, ", min_size=", argv_predict$min_size, ", max_size=", argv_predict$max_size)

test.modules.uploaded <- enrichment_modules(
  Expr.matrix = test_expr,
  modules = Sponge.modules,
  bin.size = argv_predict$bin_size,
  min.size = argv_predict$min_size,
  max.size = argv_predict$max_size,
  min.expr = argv_predict$min_expr,
  method = argv_predict$method,
  cores = argv_predict$enrichment_cores
) %>% check_enrichment("pancancer")

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
  pancan_sufficient <- record_coverage("pancancer", trained.model$Model$coefnames, test.modules.uploaded)
  test.modules.uploaded.pancan <- test.modules.uploaded[common_modules, , drop = FALSE]
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
  if (!pancan_sufficient) {
    type_predictions <- NA
  }
  # build table with results
  predictions <- data.frame(sampleID = samples, typePrediction = type_predictions, subtypePrediction = NA)
  type_splits <- list()


  #-----------------PREDICT SUB-TYPES FOR TYPE PREDICTIONS------------------------
  # without a type prediction there is nothing to split on (split() would drop every sample)
  if (argv_predict$subtypes && pancan_sufficient) {
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
          ) %>% check_enrichment(type_renamed)
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
      # A type whose per-type enrichment failed/returned NULL would make NULL[, samples] throw
      # ("incorrect number of dimensions") and abort the whole prediction. Skip it (subtype NA).
      mod_mat <- test.modules.updated.types[[type]]
      if (is.null(mod_mat)) {
        # below SAMPLES_THRESHOLD no subtype is predicted anyway, so don't report it as low coverage
        if (type_clean %in% names(models) && length(samples) >= SAMPLES_THRESHOLD) {
          record_coverage(type_clean, models[[type_clean]]$model$Model$coefnames, NULL)
        }
        df$subtypePrediction <- NA
        return(df)
      }
      modules <- mod_mat[, samples, drop = FALSE]
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
  if (!model_name %in% names(models)) {
    stop("Unknown model '", argv_predict$model, "' for ", level, " level; available: ", paste(names(models), collapse = ", "))
  }
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
  ) %>% check_enrichment(model_name)

  # do hierarchical clustering on enrichment scores on genes and samples (guarded for n >= 2)
  if (!is.null(test.modules.uploaded.type) && nrow(test.modules.uploaded.type) >= 2) {
    row_order <- hclust(dist(test.modules.uploaded.type, method = "euclidean"), method = "ward.D2")$order
    test.modules.uploaded.type <- test.modules.uploaded.type[row_order, , drop = FALSE]
  }
  if (!is.null(test.modules.uploaded.type) && ncol(test.modules.uploaded.type) >= 2) {
    col_order <- hclust(dist(t(test.modules.uploaded.type), method = "euclidean"), method = "ward.D2")$order
    test.modules.uploaded.type <- test.modules.uploaded.type[, col_order, drop = FALSE]
  }

  # do subtype prediction only on specified type
  if (argv_predict$subtypes) {
    message(Sys.time(), " - predicting subtype")
    # must be the type-specific enrichment: the type model's coefnames are type module names,
    # which barely overlap with the pancancer modules in test.modules.uploaded.
    # Re-subset to `samples`: the columns were reordered by clustering above, and the returned
    # vector is assigned positionally to `predictions` (built in colnames(test_expr) order).
    subtypePrediction <- predict_subtype(
      type = model_name,
      sample_list = samples,
      all_models = models,
      test_modules = test.modules.uploaded.type[, samples, drop = FALSE],
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
  # Collapse to a single value: ties return >1 name and an all-NA table returns character(0);
  # either would make data.frame() build a multi-row/zero-row meta (FE reads meta[0]) or throw.
  type_predict = if (length(dominant_type) == 0) "NA" else dominant_type[1],
  subtype_predict = if (length(dominant_subtype) == 0) "NA" else dominant_subtype[1],
  specified_type = argv_predict$model,
  script_version = "0.1.4"
) # see changelog at the bottom

# feature coverage: scalar fields for the model behind the headline prediction (the specified
# type's subtype model, else the pancancer type model), plus one entry per model used
specified_model <- !(is.null(argv_predict$model) || argv_predict$model == "None" || argv_predict$model == "pancancer" || argv_predict$model == "Pancancer")
primary_model <- if (specified_model) gsub("&", "and", gsub(" ", "_", argv_predict$model)) else "pancancer"
primary_coverage <- module_coverage[[primary_model]]
meta$modules_matched <- if (is.null(primary_coverage)) NA else primary_coverage$modules_matched
meta$modules_expected <- if (is.null(primary_coverage)) NA else primary_coverage$modules_expected
meta$low_coverage <- if (is.null(primary_coverage)) NA else primary_coverage$low_coverage
meta$module_coverage <- list(if (length(module_coverage) > 0) do.call(rbind, unname(module_coverage)) else list())

# return as JSON for API processing
scores_df <- as.data.frame(test.modules.uploaded)
scores_list <- list(
  samples = colnames(scores_df),
  genes = rownames(scores_df),
  values = lapply(seq_len(nrow(scores_df)), function(i) {
    as.numeric(scores_df[i, ])
  })
)
# append type-specific scores
# NOTE: this condition must mirror the branch condition used above (line ~218) to decide
# between "predict pancancer + per-type enrichment" vs. "enrich only the specified type" -
# otherwise a model of "pancancer"/"None" would incorrectly try to use
# test.modules.uploaded.type, which is only computed in the specified-model branch.
if (argv_predict$subtypes) {
  if (!(is.null(argv_predict$model) || argv_predict$model == "None" || argv_predict$model == "pancancer" || argv_predict$model == "Pancancer")) {
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

# Build module members dictionary only for relevant scopes
module_members <- list()
module_members[["pancancer"]] <- models$expression_across_types$modules
module_members[["expression_across_types"]] <- models$expression_across_types$modules

relevant_types <- c()
if (!(is.null(argv_predict$model) || argv_predict$model == "None" || argv_predict$model == "pancancer" || argv_predict$model == "Pancancer")) {
  # Specified model
  relevant_types <- c(relevant_types, argv_predict$model)
}
if (!is.null(predictions) && "typePrediction" %in% colnames(predictions)) {
  # Predicted models
  pred_types <- unique(predictions$typePrediction)
  pred_types <- pred_types[!is.na(pred_types)]
  relevant_types <- c(relevant_types, pred_types)
}

relevant_types <- unique(relevant_types)
for (type in relevant_types) {
  # Clean type to match models keys (underscores, "and")
  type_clean <- gsub("&", "and", gsub(" ", "_", type))
  if (type_clean %in% names(models)) {
    mods <- models[[type_clean]]$modules

    # Store under clean name
    module_members[[type_clean]] <- mods

    # Store under display name (with spaces and ampersands)
    display_name <- gsub("and", "&", gsub("_", " ", type_clean))
    module_members[[display_name]] <- mods

    # Store under display name (with spaces and "and")
    display_name_and <- gsub("_", " ", type_clean)
    module_members[[display_name_and]] <- mods
  }
}

responseObj <- list(meta = meta, data = predictions, scores = scores_list, type_scores = type_scores, module_members = module_members)

message(Sys.time(), " - FINISHED EXECUTION")
message("Writing output file to ", argv_predict$output)
message("Metadata summary: runtime=", meta$runtime, "s, level=", meta$level, ", n_samples=", meta$n_samples)
write_json(responseObj, path = argv_predict$output)

################################################################################
##                                 Changelog                                  ##
################################################################################


# 0.1.4
# - subtype prediction for a specified --model now uses the type-specific enrichment
#   (test.modules.uploaded.type, re-subset to upload sample order) instead of the pancancer
#   one, which shared almost no features with the type model and made it predict on noise
# - fail fast when enrichment_modules() returns no scores (e.g. unknown method spelling)
# - per-model feature coverage logged and returned in meta (modules_matched,
#   modules_expected, low_coverage, module_coverage); predictions with coverage below
#   COVERAGE_THRESHOLD are returned as NA
# - unknown --model stops with the list of available models

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
