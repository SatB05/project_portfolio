# -*- coding: utf-8 -*-
"""4. TwitterHater.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1B6i0GOS_xcNYo62vRSP1-0PckH7fq-S-

# **Loading Libraries**
"""

# EDA & Text Processing
import numpy as np
import pandas as pd
import re
# Model Building
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.pipeline import Pipeline
# DL model imports
import tensorflow_hub as hub
from sklearn.preprocessing import LabelEncoder
import tensorflow as tf
from transformers import AutoTokenizer, TFAutoModelForSequenceClassification
from transformers import BertTokenizer, TFBertModel
from transformers import pipeline

"""# **Exploring Dataframe**"""

df = pd.read_csv('/content/train_E6oV3lV-3.csv')
df.info()

df.head()

"""## **Text Processing**"""

def clean_text(text):
    text = re.sub(r'@[\w]*', '', text)  # subbing out mentions
    text = re.sub(r'#', '', text)  # subbing out hashtags
    text = re.sub(r'https?://\S+|www\.\S+', '', text)  # subbing out URLs
    text = re.sub(r'[^A-Za-z\s]', '', text)  # subbing out special characters
    text = text.lower()  # Converting to lowercase
    return text

df['clean_text'] = df['tweet'].apply(clean_text)

df['clean_text'].head()

df['clean_text'].str.len().max()

"""## Train-Test Split"""

X_train, X_test, y_train, y_test = train_test_split(df['clean_text'], df['label'], test_size=0.2, random_state=10)

"""# **Frequency-based Text Embedding**

  > ### Bag of Words
"""

# Bag of words
bow_vectorizer = CountVectorizer(max_features = 10000)
X_train_bow = bow_vectorizer.fit_transform(X_train)
X_test_bow = bow_vectorizer.transform(X_test)

"""    > Creating Pipeline and Hyperparameter Tuning"""

bow_pipe = Pipeline([
    ('classifier', LogisticRegression())
])

param_grid = [
    # Logistic Regression
    {'classifier': [LogisticRegression(max_iter=2000)],
     'classifier__C': np.logspace(-3, 3, 15),
     'classifier__penalty': ['l1', 'l2'],
     'classifier__solver': ['liblinear']},
    # RandomForestClassifier
    {'classifier': [RandomForestClassifier()],
     'classifier__n_estimators': [50, 100],
     'classifier__max_features': ['sqrt', 'log2'],
     'classifier__max_depth': [None, 10, 20]}
]

results = pd.DataFrame(columns=['Model', 'Training Accuracy', 'Test Accuracy'])

for params in param_grid:
  # setup Pipeline with the current Classifier
  bow_pipe.set_params(**{k: v[0] for k, v in params.items()})
  grid_search = GridSearchCV(bow_pipe, param_grid= [params], cv=10, scoring='accuracy', n_jobs=-1)
  grid_search.fit(X_train_bow, y_train)

  # extracting the best metrics and evaluating current Classifier
  best_model = grid_search.best_estimator_
  train_acc = best_model.score(X_train_bow, y_train)*100
  test_acc = best_model.score(X_test_bow, y_test)*100

  # recording findings into a temporary df
  temp_df = pd.DataFrame({
        'Model': [type(best_model.named_steps['classifier']).__name__ + '_bow'],
        'Training Accuracy': [train_acc],
        'Test Accuracy': [test_acc]
    })

  #finalising entry into the findings df
  results = pd.concat([results, temp_df], ignore_index=True)

"""  > ### TF-IDF Vectorizor"""

# TF-IDF
tfidf_vectorizer = TfidfVectorizer(max_features = 10000)
X_train_tfidf = tfidf_vectorizer.fit_transform(X_train)
X_test_tfidf = tfidf_vectorizer.transform(X_test)

"""    > Creating Pipeline and Hyperparameter Tuning"""

tfidf_vectorizer_pipe = Pipeline([
    ('classifier', LogisticRegression())
])

param_grid = [
    # Logistic Regression
    {'classifier': [LogisticRegression(max_iter=2000)],
     'classifier__C': np.logspace(-3, 3, 15),
     'classifier__penalty': ['l1', 'l2'],
     'classifier__solver': ['liblinear']},
    # RandomForestClassifier
    {'classifier': [RandomForestClassifier()],
     'classifier__n_estimators': [50, 100],
     'classifier__max_features': ['sqrt', 'log2'],
     'classifier__max_depth': [None, 10, 20]}
]

for params in param_grid:
  # setup Pipeline with the current Classifier
  tfidf_vectorizer_pipe.set_params(**{k: v[0] for k, v in params.items()})
  grid_search = GridSearchCV(tfidf_vectorizer_pipe, param_grid= [params], cv=10, scoring='accuracy', n_jobs=-1)
  grid_search.fit(X_train_bow, y_train)

  # extracting the best metrics and evaluating current Classifier
  best_model = grid_search.best_estimator_
  train_acc = best_model.score(X_train_tfidf, y_train)*100
  test_acc = best_model.score(X_test_tfidf, y_test)*100

  # recording findings into a temporary df
  temp_df = pd.DataFrame({
        'Model': [type(best_model.named_steps['classifier']).__name__ + '_tfidf'],
        'Training Accuracy': [train_acc],
        'Test Accuracy': [test_acc]
    })

  #finalising entry into the findings df
  results = pd.concat([results, temp_df], ignore_index=True)

"""# **Semantic & Contextual Text Embedding Techniques**


> # roBERTa
  The RoBERTa-base model is trained on ~124M tweets from January 2018 to December 2021, and finetuned for sentiment analysis with the TweetEval benchmark. For further details on the model [click here](https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment-latest)
"""

model_name = "cardiffnlp/twitter-roberta-base-sentiment-latest"
model = TFAutoModelForSequenceClassification.from_pretrained(model_name, from_pt= True)
tokenizer = AutoTokenizer.from_pretrained(model_name)
classifier= pipeline('sentiment-analysis', model=model, tokenizer= tokenizer)

classifier('amazing!')[0]['label']

model_name = "cardiffnlp/twitter-roberta-base-sentiment-latest"
model = TFAutoModelForSequenceClassification.from_pretrained(model_name, from_pt= True)
tokenizer = AutoTokenizer.from_pretrained(model_name)

"""      > Mapping Default Model labels to corresponding Target Encoded values in binary."""

def sentiment_mapper(sentiment_label):
  """
  > "LABEL_0" == 'negative'(hate)  tweet
  > "LABEL_1" == 'neutral' tweet
  > "LABEL_2" == 'positive' tweet
  """

  if sentiment_label ==  'LABEL_0':
    return 1
  else:
    return 0

def batch_predict(data, batch_size=761):
    label_vals = []
    for i in range(0, len(data), batch_size):
        batch = data[i:i+batch_size]

        # Tokenizing the batch
        inputs = tokenizer(batch, return_tensors="tf", padding=True, truncation=True, max_length=512)

        # Running predictions for the batch
        outputs = model(inputs['input_ids'], attention_mask=inputs['attention_mask'])
        probs = tf.nn.softmax(outputs.logits, axis=-1)
        preds = np.argmax(probs, axis=1)

        # Converting model predictions to binary
        labels = [sentiment_mapper(f'LABEL_{p}') for p in preds]
        label_vals.extend(labels)
    return label_vals

X_train.dtypes

train_preds = batch_predict(X_train.astype(str).tolist())
test_preds = batch_predict(X_test.astype(str).tolist())

train_acc = accuracy_score(train_preds, y_train) * 100
test_acc = accuracy_score(test_preds, y_test) * 100

temp_df = pd.DataFrame({
    'Model': ['roBERTa'],
    'Training Accuracy': [train_acc],
    'Test Accuracy': [test_acc]
})

results = pd.concat([results, temp_df], ignore_index=True)

"""  > # Universal Sentence Encoder
   The Universal Sentence Encoder encodes text into high dimensional vectors that can be used for text classification, semantic similarity, clustering and other natural language tasks.The model is trained and optimized for greater-than-word length text, such as sentences, phrases or short paragraphs. It is trained on a variety of data sources and a variety of tasks with the aim of dynamically accommodating a wide variety of natural language understanding tasks.
   For more details on the model [click here](https://www.kaggle.com/models/google/universal-sentence-encoder/tensorFlow2/universal-sentence-encoder/2?tfhub-redirect=true).
"""

url = "https://tfhub.dev/google/universal-sentence-encoder/4"
embed = hub.load(url)

def get_embeddings(data):
  return embed(data).numpy()

X_train_embeddings = get_embeddings(X_train)
X_test_embeddings = get_embeddings(X_test)

"""      > Training a Logistic Regression and Random Forest model on USE."""

logistic_model = LogisticRegression(max_iter=1000)
logistic_model.fit(X_train_embeddings, y_train)


train_acc_logistic = logistic_model.score(X_train_embeddings, y_train) * 100
test_acc_logistic = logistic_model.score(X_test_embeddings, y_test) * 100

print(f'Logistic Regression - Training Accuracy: {train_acc_logistic:.2f}%')
print(f'Logistic Regression - Test Accuracy: {test_acc_logistic:.2f}%')

rf_model = RandomForestClassifier()
rf_model.fit(X_train_embeddings, y_train)


train_acc_rf = rf_model.score(X_train_embeddings, y_train) * 100
test_acc_rf = rf_model.score(X_test_embeddings, y_test) * 100

print(f'Random Forest - Training Accuracy: {train_acc_rf:.2f}%')
print(f'Random Forest - Test Accuracy: {test_acc_rf:.2f}%')

temp_df = pd.DataFrame({
    'Model': ['LogisticRegression_USE'],
    'Training Accuracy': [train_acc_logistic],
    'Test Accuracy': [test_acc_logistic]
})

results = pd.concat([results, temp_df], ignore_index=True)

temp_df = pd.DataFrame({
    'Model': ['RamdomForestClassifier_USE'],
    'Training Accuracy': [train_acc_rf],
    'Test Accuracy': [test_acc_rf]
})

results = pd.concat([results, temp_df], ignore_index=True)

"""# **Final Result**"""

results