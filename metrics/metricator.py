#!/usr/bin/env python

from pyspark.sql import SparkSession

spark = SparkSession \
    .builder \
    .appName("myApp") \
    .config("spark.mongodb.input.uri", "mongodb://127.0.0.1/trace_database.fs.files") \
    .config("spark.mongodb.output.uri", "mongodb://127.0.0.1/test.metric") \
    .getOrCreate()


df = spark.read.format("com.mongodb.spark.sql.DefaultSource").load()
df.show()
