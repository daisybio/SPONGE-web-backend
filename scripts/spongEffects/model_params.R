# Training parameters of the spongEffects models in models.RDS, shared by classify.R and
# describe_models.R.
#
# A model's enrichment must be computed with the parameters it was trained with (method, module size
# window, bin size, min_expr); the network thresholds (m_scor_threshold, p_adj_threshold) only
# describe how its modules were built. Sources, first match wins:
#   1. models[[level]][[key]]$params  - written by the training script (preferred for new models), a
#      named list with the fields in PARAM_FIELDS
#   2. the fallback JSON (models_params_fallback.json next to this file) - for models.RDS files
#      without $params; an entry only applies if its n_features equals the model's number of
#      features (length(coefnames)), so a replaced models.RDS never picks up stale values
#   3. NULL - the caller falls back to the request's parameters
PARAM_FIELDS <- c(
  "method", "bin_size", "min_size", "max_size", "min_expr",
  "m_scor_threshold", "p_adj_threshold", "train_split"
)

read_params_fallback <- function(path) {
  if (is.null(path) || is.na(path) || !file.exists(path)) {
    return(list())
  }
  jsonlite::fromJSON(path, simplifyVector = FALSE)$models
}

# keeps the known fields with a value (a NULL would make modifyList() drop the default)
clean_params <- function(p) Filter(Negate(is.null), p[intersect(PARAM_FIELDS, names(p))])

# Returns list(params = <named list or NULL>, source = "model" | "fallback" | NA)
lookup_model_params <- function(models_level, level, key, fallback) {
  entry <- models_level[[key]]
  if (is.null(entry)) {
    return(list(params = NULL, source = NA_character_))
  }
  if (!is.null(entry$params)) {
    return(list(params = clean_params(entry$params), source = "model"))
  }
  fb <- fallback[[level]][[key]]
  n_features <- length(entry$model$Model$coefnames)
  if (!is.null(fb) && identical(as.integer(fb$n_features), as.integer(n_features))) {
    return(list(params = clean_params(fb), source = "fallback"))
  }
  list(params = NULL, source = NA_character_)
}
