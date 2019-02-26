library(rwebppl)
library(tidyverse)
library(jsonlite)
library(ggthemes)
library(pander)

project_dir = "../"
data_dir = function(path) {
  return(paste(project_dir, "data/", path, sep = ""))
}
cache_dir = function(path) {
  return(paste(project_dir, "analysis/.cache/", path, sep = ""))
}
model_dir = function(path) {
  return(paste(project_dir, "models/", path, sep = ""))
}

char = as.character
num = function(v) {
  v = ifelse(is.na(v), NA, char(v))
  v = ifelse(v=="infty", "Inf", v)
  v = as.numeric(v)
  return(v)
}

theme.new = theme_set(theme_few(12))

# for bootstrapping 95% confidence intervals
theta <- function(x,xdata) {mean(xdata[x])}
ci.low <- function(x) {
  quantile(bootstrap::bootstrap(1:length(x),1000,theta,x)$thetastar,.025)}
ci.high <- function(x) {
  quantile(bootstrap::bootstrap(1:length(x),1000,theta,x)$thetastar,.975)}

named_vec = function(df, label_vec, value_vec) {
  if (!is.null(df)) {
    label_vec <- df[[deparse(substitute(label_vec))]]
    value_vec <- df[[deparse(substitute(value_vec))]]
  }
  names(value_vec) = label_vec
  return(value_vec)
}

change_names = function(df, new_names) {
  names(df) = new_names
  return(df)
}

approx_eq = function(a, b, eps=0.0000001) {
  return(abs(a-b) < eps)
}
