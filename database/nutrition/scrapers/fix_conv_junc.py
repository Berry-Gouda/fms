import pandas as pd

# Load lookup table and main data
conv_junc = pd.read_csv('/home/bg-labs/bg_labs/fms/database/nutrition/data/conversion_junc.csv')
unit_lu = pd.read_csv('/home/bg-labs/bg_labs/fms/database/nutrition/data/unit_lu.csv')

# Function to process the column
def process_column(value):
    if value == -1:
        return 2
    else:
        return value

# Apply transformation
conv_junc['amt_unit'] = conv_junc['amt_unit'].apply(process_column)

print(conv_junc.head())

conv_junc.to_csv('/home/bg-labs/bg_labs/fms/database/nutrition/data/conversion_junc.csv', index=False)