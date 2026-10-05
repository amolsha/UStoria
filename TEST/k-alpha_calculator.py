import pandas as pd
import krippendorff

# Read CSV
df = pd.read_csv("ratings.csv")

# 🔴 DROP item identifier column
df = df.drop(columns=["Item"])

# Convert to numpy & transpose (raters × items)
data = df.to_numpy(dtype=float).T

print("Data shape:", data.shape)  # should be (3, number_of_items)

alpha_nominal = krippendorff.alpha(
    reliability_data=data,
    level_of_measurement="nominal"
)

alpha_ordinal = krippendorff.alpha(
    reliability_data=data,
    level_of_measurement="ordinal"
)

print("Alpha nominal:", round(alpha_nominal, 3))
print("Alpha ordinal:", round(alpha_ordinal, 3))
