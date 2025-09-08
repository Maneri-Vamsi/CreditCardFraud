import pandas as pd
import numpy as np

num_samples = 300  # total samples
half_samples = num_samples // 2  # 150 genuine, 150 fraud

# Generate genuine transactions (fraud_label = 0)
bio_genuine = np.random.choice([0, 1], size=half_samples, p=[0.1, 0.9])
amount_genuine = np.random.randint(100, 7000, size=half_samples)  # keep lower amounts to reduce fraud chance
foreign_genuine = np.random.choice([0, 1], size=half_samples, p=[0.8, 0.2])
fraud_label_genuine = [0]*half_samples

# Generate fraudulent transactions (fraud_label = 1)
bio_fraud = np.random.choice([0, 1], size=half_samples, p=[0.3, 0.7])
amount_fraud = np.random.randint(7001, 10001, size=half_samples)  # higher amounts
foreign_fraud = np.random.choice([0, 1], size=half_samples, p=[0.2, 0.8])
fraud_label_fraud = [1]*half_samples

# Combine genuine and fraud samples
biometric_verified = np.concatenate([bio_genuine, bio_fraud])
amount = np.concatenate([amount_genuine, amount_fraud])
foreign = np.concatenate([foreign_genuine, foreign_fraud])
fraud_label = np.concatenate([fraud_label_genuine, fraud_label_fraud])

# Shuffle the dataset
indices = np.arange(num_samples)
np.random.shuffle(indices)

df = pd.DataFrame({
    'biometric_verified': biometric_verified[indices],
    'amount': amount[indices],
    'foreign': foreign[indices],
    'fraud_label': fraud_label[indices]
})

df.to_csv('synthetic_fraud_dataset_balanced.csv', index=False)
print("Balanced dataset generated: synthetic_fraud_dataset_balanced.csv")
