import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import os

CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Data/training_data.csv")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Data/model.pkl")
MIN_KEYS = 5

df = pd.read_csv(CSV)
df = df[df['key_count'] >= MIN_KEYS].reset_index(drop=True)

print(f"Rows after filtering: {len(df)}")
print(f"Label distribution:\n{df['label'].value_counts().to_string()}\n")

X = df[['key_count', 'avg_gap', 'variance']].values
y = df['label'].values

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

model = RandomForestClassifier(
    n_estimators=200,
    class_weight='balanced',
    random_state=42
)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
print("=== Test set results ===")
print(classification_report(y_test, y_pred, target_names=["human", "malicious"]))

print("=== Confusion matrix (human / malicious) ===")
cm = confusion_matrix(y_test, y_pred)
print(f"  Predicted human | Predicted malicious")
print(f"  Human:      {cm[0][0]:>5}  |  {cm[0][1]:>5}")
print(f"  Malicious:  {cm[1][0]:>5}  |  {cm[1][1]:>5}\n")

cv_scores = cross_val_score(model, X, y, cv=5, scoring='f1')
print(f"5-fold CV F1: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")

importances = model.feature_importances_
features = ['key_count', 'avg_gap', 'variance']
print("\nFeature importances:")
for f, imp in sorted(zip(features, importances), key=lambda x: -x[1]):
    print(f"  {f}: {imp:.3f}")

joblib.dump(model, OUT)
print(f"\nModel saved to {OUT}")
