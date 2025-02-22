# -*- coding: utf-8 -*-
"""CNN.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/13fQhK4JEXGpz6PybgVPRxvG1Qa_8uQpf
"""

! pip install kaggle

from google.colab import files
uploaded = files.upload()

!mkdir ~/.kaggle

!cp kaggle.json ~/.kaggle/

! chmod 600 ~/.kaggle/kaggle.json

! kaggle datasets list

!kaggle competitions download -c isic-2024-challenge

!unzip isic-2024-challenge.zip

import pandas as pd

# Baca file CSV dengan path lengkap
df_train = pd.read_csv('train-metadata.csv', low_memory=False)
df_test = pd.read_csv('test-metadata.csv', low_memory=False)
df_sub = pd.read_csv('sample_submission.csv')

# Verifikasi isi dari dataframes
print(df_train.head())
print(df_train.info())
print(df_test.head())
print(df_test.info())
print(df_sub.head())

df_train.describe(include='all')

print(df_train.columns.tolist())

features_cat =['sex', 'anatom_site_general', 'image_type', 'tbp_tile_type',
               'tbp_lv_location', 'tbp_lv_location_simple', 'attribution', 'copyright_license']
features_num = ['age_approx', 'clin_size_long_diam_mm', 'tbp_lv_A', 'tbp_lv_Aext', 'tbp_lv_B', 'tbp_lv_Bext',
                'tbp_lv_C', 'tbp_lv_Cext', 'tbp_lv_H', 'tbp_lv_Hext', 'tbp_lv_L', 'tbp_lv_Lext', 'tbp_lv_areaMM2',
                'tbp_lv_area_perim_ratio', 'tbp_lv_color_std_mean', 'tbp_lv_deltaA', 'tbp_lv_deltaB',
                'tbp_lv_deltaL', 'tbp_lv_deltaLB', 'tbp_lv_deltaLBnorm', 'tbp_lv_eccentricity',
                'tbp_lv_minorAxisMM', 'tbp_lv_nevi_confidence', 'tbp_lv_norm_border', 'tbp_lv_norm_color',
                'tbp_lv_perimeterMM', 'tbp_lv_radial_color_std_max', 'tbp_lv_stdL', 'tbp_lv_stdLExt', 'tbp_lv_symm_2axis', 'tbp_lv_symm_2axis_angle',
                'tbp_lv_x', 'tbp_lv_y', 'tbp_lv_z']
target = 'target'

import os

# Verifikasi isi direktori
image_dir = '/content/train-image'
print(os.listdir(image_dir))

import pandas as pd
import numpy as np
import h5py
import time
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import GlobalAveragePooling2D, Dropout, Dense
from tensorflow.keras.applications import EfficientNetB0
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.image import resize
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from skimage.transform import resize
import numpy as np

def preprocess_images(image_dict, target_size=(150, 150)):
    images = []
    ids = []
    for key, img in image_dict.items():
        img_resized = resize(img, target_size + (3,), mode='reflect')  # Adding 3 for RGB channels
        img_resized = img_resized.astype('float32') / 255.0  # Normalize
        images.append(img_resized)
        ids.append(key)
    return np.array(images), ids

train_images = {
    'img1': np.array([[255, 0], [0, 255]]),
    'img2': np.array([[0, 255], [255, 0]])
}
test_images = {
    'img3': np.array([[128, 128], [128, 128]]),
    'img4': np.array([[255, 255], [0, 0]])
}

X_train_images, train_ids = preprocess_images(train_images)
X_test_images, test_ids = preprocess_images(test_images)

print("X_train_images shape:", X_train_images.shape)
print("X_test_images shape:", X_test_images.shape)

df_train_filtered = df_train[df_train['isic_id'].isin(train_ids)]
y_train = df_train_filtered['target'].values
print("Number of samples in y_train:", len(y_train))
print("X_train_images shape:", X_train_images.shape)
print("y_train length:", len(y_train))

X_train_images = np.random.random((100, 150, 150, 3))  # Replace with your actual image data
y_train = np.random.randint(0, 2, size=(100,))  # Replace with your actual labels

X_train_images = X_train_images[:2000]  # Menggunakan hanya 2000 gambar
y_train = y_train[:2000]

datagen = ImageDataGenerator(
    rescale=1./255,
    rotation_range=30,
    width_shift_range=0.3,
    height_shift_range=0.3,
    shear_range=0.3,
    zoom_range=0.3,
    horizontal_flip=True,
    fill_mode='nearest',
    validation_split=0.2  # Split 80% train, 20% validation
)

val_datagen = ImageDataGenerator(rescale=1./255)

train_generator = datagen.flow_from_directory(
    image_dir,
    target_size=(150, 150),
    batch_size=64,
    class_mode='binary',
    subset='training'
)

val_generator = datagen.flow_from_directory(
    image_dir,
    target_size=(150, 150),
    batch_size=64,
    class_mode='binary',
    subset='validation'
)

train_batch = next(train_generator)
val_batch = next(val_generator)

print("Train batch shape:", train_batch[0].shape, train_batch[1].shape)
print("Validation batch shape:", val_batch[0].shape, val_batch[1].shape)

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from tensorflow.keras.regularizers import l2

# Bangun model CNN dengan Dropout dan Batch Normalization
model = Sequential([
    Conv2D(32, (3, 3), activation='relu', input_shape=(150, 150, 3), kernel_regularizer=l2(0.001)),
    BatchNormalization(),
    MaxPooling2D(2, 2),
    Dropout(0.3),

    Conv2D(64, (3, 3), activation='relu', kernel_regularizer=l2(0.001)),
    BatchNormalization(),
    MaxPooling2D(2, 2),
    Dropout(0.3),

    Conv2D(128, (3, 3), activation='relu', kernel_regularizer=l2(0.001)),
    BatchNormalization(),
    MaxPooling2D(2, 2),
    Dropout(0.4),

    Flatten(),
    Dense(512, activation='relu', kernel_regularizer=l2(0.001)),
    BatchNormalization(),
    Dropout(0.5),
    Dense(1, activation='sigmoid')
])

model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
model.summary()

import tensorflow as tf

class TerminateOnNaN(tf.keras.callbacks.Callback):
    def on_epoch_end(self, epoch, logs=None):
        if epoch == 10:  # Hentikan setelah 10 epoch
            self.model.stop_training = True

# Menambahkan callback ke dalam pelatihan
terminate_on_nan = TerminateOnNaN()

# Callback untuk Early Stopping dan Model Checkpoint
early_stopping = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
model_checkpoint = ModelCheckpoint('my_model.keras', save_best_only=True)
reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=5)

# Jumlah langkah per epoch untuk training dan validation
steps_per_epoch = 100
validation_steps = 50

# Melatih model dengan generator
history = model.fit(
    train_generator,
    steps_per_epoch=steps_per_epoch,
    epochs=30,
    validation_data=val_generator,
    validation_steps=validation_steps,
    callbacks=[early_stopping, model_checkpoint, reduce_lr]
)

import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

# Load best model weights
model.load_weights('my_model.keras')

# Prediksi pada data validasi
val_generator.reset()
predictions = model.predict(val_generator)
val_predictions = (predictions > 0.5).astype('int32').flatten()  # Pastikan val_predictions dalam bentuk array 1D

# Ambil label sebenarnya dari generator validasi
val_labels = val_generator.classes

# Hitung metrik evaluasi
accuracy = accuracy_score(val_labels, val_predictions)
precision = precision_score(val_labels, val_predictions)
recall = recall_score(val_labels, val_predictions)
f1 = f1_score(val_labels, val_predictions)
cm = confusion_matrix(val_labels, val_predictions)

print(f'Validation Accuracy: {accuracy:.4f}')
print(f'Validation Precision: {precision:.4f}')
print(f'Validation Recall: {recall:.4f}')
print(f'Validation F1 Score: {f1:.4f}')
print(f'Confusion Matrix:\n{cm}')

# Plot training history
plt.figure(figsize=(12, 4))
plt.subplot(1, 2, 1)
plt.plot(history.history['accuracy'], label='Train Accuracy')
plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
plt.legend()
plt.title('Accuracy')

plt.subplot(1, 2, 2)
plt.plot(history.history['loss'], label='Train Loss')
plt.plot(history.history['val_loss'], label='Validation Loss')
plt.legend()
plt.title('Loss')

plt.show()

# Generate predictions
predictions = model.predict(X_test_images)git
# Prepare the DataFrame in the required format
submission_df = pd.DataFrame({
    'isic_id': test_ids,  # Assuming test_ids contains the IDs of your test images
    'target': predictions.flatten()  # Flatten if predictions are not already a 1D array
})

# Save to CSV
submission_df.to_csv('submission.csv', index=False)