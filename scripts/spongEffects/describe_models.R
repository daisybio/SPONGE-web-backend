#!/usr/bin/env Rscript
# Writes a JSON description of the models in a models.RDS for the API (GET /spongEffects/predictionModels):
#   {"gene": {"<model key>": {"params": {...training parameters...}, "params_source": "model"|"fallback"|null,
#                             "n_features": int, "n_modules": int, "test_accuracy": num}}, "transcript": {...}}
# usage: describe_models.R --model_path models.RDS --output models.json [--params_fallback file.json]
suppressWarnings(suppressPackageStartupMessages({
  library(argparser)
  library(jsonlite)
}))

parser <- arg_parser("Describe spongEffects models")
parser <- add_argument(parser, "--model_path", help = "Path to spongEffects models RDS object")
parser <- add_argument(parser, "--output", help = "Output JSON")
parser <- add_argument(parser, "--params_fallback", help = "JSON with training parameters for models without $params", default = NA)
argv <- parse_args(parser)

script_dir <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])))
source(file.path(script_dir, "model_params.R"))
fallback <- read_params_fallback(if (is.na(argv$params_fallback)) file.path(script_dir, "models_params_fallback.json") else argv$params_fallback)

models_raw <- readRDS(argv$model_path)
out <- lapply(setNames(names(models_raw), names(models_raw)), function(level) {
  lapply(setNames(names(models_raw[[level]]), names(models_raw[[level]])), function(key) {
    entry <- models_raw[[level]][[key]]
    found <- lookup_model_params(models_raw[[level]], level, key, fallback)
    accuracy <- entry$model$ConfusionMatrix_testing$overall[["Accuracy"]]
    list(
      params = found$params,
      params_source = if (is.na(found$source)) NULL else found$source,
      n_features = length(entry$model$Model$coefnames),
      n_modules = length(entry$modules),
      test_accuracy = if (is.null(accuracy)) NULL else unname(accuracy)
    )
  })
})
write_json(out, argv$output, auto_unbox = TRUE, null = "null", digits = NA)
