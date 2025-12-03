from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, IntegerType, StringType
import random

# Initialize Spark
spark = SparkSession.builder.appName("GenerateCustomerComments").enableHiveSupport().getOrCreate()

# ---- PARAMETERS ----
NUM_CUSTOMERS = 10000     # assuming customer_dim has up to 1000 customers
NUM_COMMENTS = 100000     # total comments to generate

# ---- SAMPLE COMMENT POOL ----
positive_comments = [
    "Amazing flight experience!",
    "Loved the service and comfort.",
    "Excellent crew, smooth flight.",
    "Best airline I’ve flown with.",
    "Fantastic food and friendly staff.",
    "Quick boarding and comfortable seats.",
    "Everything was perfect.",
    "Loved the entertainment system.",
    "Very professional crew.",
    "Great value for money!"
]

negative_comments = [
    "Horrible experience, flight delayed for hours.",
    "Seats were very uncomfortable.",
    "My luggage was lost and no one helped.",
    "Customer service was rude.",
    "The food was terrible.",
    "Long queues and poor management.",
    "Flight was cancelled without notice.",
    "Very noisy and dirty cabin.",
    "Crew ignored my requests.",
    "I’ll never fly with this airline again."
]

neutral_comments = [
    "Average experience, nothing special.",
    "Flight was okay but could be better.",
    "Not too bad, not too good.",
    "Service was fine.",
    "Typical flight experience.",
    "The check-in process was normal.",
    "It was just another flight.",
    "Had an acceptable journey.",
    "Neutral impression overall.",
    "Flight time was as expected."
]

# ---- COMMENT GENERATION ----
data = []
for _ in range(NUM_COMMENTS):
    custkey = random.randint(1, NUM_CUSTOMERS)
    sentiment = random.choices(
        ["positive", "negative", "neutral"], 
        weights=[0.4, 0.3, 0.3], 
        k=1
    )[0]
    
    if sentiment == "positive":
        comment = random.choice(positive_comments)
    elif sentiment == "negative":
        comment = random.choice(negative_comments)
    else:
        comment = random.choice(neutral_comments)
    
    data.append((custkey, comment))

# ---- SCHEMA & SAVE ----
schema = StructType([
    StructField("custkey", IntegerType(), False),
    StructField("comment", StringType(), False)
])

comments_df = spark.createDataFrame(data, schema)

# Save to raw zone (Hive/Spark catalog)
comments_df.write.mode("overwrite").saveAsTable("raw.customer_comments")


print(f"✅ Successfully generated {NUM_COMMENTS} random comments for {NUM_CUSTOMERS} customers.")
print("Table saved as raw.customer_comments")

spark.stop()
