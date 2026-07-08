#!/usr/bin/env Rscript
args <- commandArgs(trailingOnly = TRUE)
model_path <- args[1]
out_dir <- args[2]

if (is.na(model_path) || is.na(out_dir)) {
  stop("Usage: Rscript extract_tcga.R <model_path> <out_dir>")
}

if (!dir.exists(out_dir)) {
  dir.create(out_dir, recursive = TRUE)
}

models_raw <- readRDS(model_path)

for (level in c("gene", "transcript")) {
  if (level %in% names(models_raw)) {
    message("Extracting TCGA training data for level: ", level)
    trained.model <- models_raw[[level]]$expression_across_types$model
    training_data <- trained.model$Model$trainingData
    
    # Save training data to csv
    write.csv(training_data, file = file.path(out_dir, paste0("tcga_", level, "_training.csv")), row.names = TRUE, quote = FALSE)
    message("Saved to: ", file.path(out_dir, paste0("tcga_", level, "_training.csv")))
  }
}
