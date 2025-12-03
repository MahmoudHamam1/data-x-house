from pyspark.sql import SparkSession
from pyspark.sql.functions import udf
from pyspark.sql.types import StringType
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Embedding, LSTM, Dense
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
import numpy as np

# Initialize Spark
spark = SparkSession.builder.appName("CustomerSentimentAnalysis").enableHiveSupport().getOrCreate()

# Load data
comments_df = spark.table("raw.customer_comments")
customer_dim = spark.table("datawarehouse.customer_dim")

# Convert Spark DataFrame to Pandas for training/inference
comments_pd = comments_df.toPandas()

# --- Tokenize and pad sequences ---
tokenizer = Tokenizer(num_words=1000, oov_token="<OOV>")
tokenizer.fit_on_texts(comments_pd["comment"])
sequences = tokenizer.texts_to_sequences(comments_pd["comment"])
padded = pad_sequences(sequences, maxlen=50, padding='post')

# --- Define simple LSTM model ---
model = Sequential([
    Embedding(1000, 16, input_length=50),
    LSTM(16),
    Dense(1, activation='sigmoid')
])

model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])

# For simplicity, simulate labels (0=negative, 1=positive)
labels = np.array([1 if "great" in c.lower() or "amazing" in c.lower() or "excellent" in c.lower() else 0 for c in comments_pd["comment"]])

# Train quickly
model.fit(padded, labels, epochs=3, verbose=0)

# Predict sentiments
predictions = model.predict(padded)
comments_pd["sentiment"] = np.where(predictions.flatten() > 0.5, "Positive", "Negative")

# Convert back to Spark DataFrame
sentiment_df = spark.createDataFrame(comments_pd[["custkey", "comment", "sentiment"]])

# Join with customer_dim
result_df = sentiment_df.join(customer_dim, on="custkey", how="left")

# Save to sandbox
result_df.write.mode("overwrite").saveAsTable("sandbox.customer_sentiment")

print("✅ Sentiment results saved to sandbox.customer_sentiment")

spark.stop()
