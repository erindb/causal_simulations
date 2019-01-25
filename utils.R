library(tidyverse)
library(jsonlite)
library(ggthemes)
library(readr)
library(ggrepel)

project_dir = "../"
results_dir = function(path) {
  return(paste(project_dir, "results/", path, sep = ""))
}

char = as.character
num = function(v) {return(as.numeric(as.character(v)))}

theme.new = theme_set(theme_few(12))

named_vec = function(df, label_vec, value_vec) {
  if (!is.null(df)) {
    label_vec <- df[[deparse(substitute(label_vec))]]
    value_vec <- df[[deparse(substitute(value_vec))]]
  }
  names(value_vec) = label_vec
  return(value_vec)
}

# fill missing values from a probability distribution
fill_df = function(df, cols) {
  expand.grid(df[cols]) %>%
    merge(df, all=T) %>%
    mutate(prob = ifelse(is.na(prob), 0, prob))
}
