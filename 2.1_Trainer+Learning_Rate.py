import os
import numpy as np
import tensorflow as tf
from PIL import Image
from tensorflow.keras import layers, models
from tensorflow.keras.optimizers import Adam


# ---------------------------
# Konfiguration
# ---------------------------
if input("Use standard configuration: ") == "yes":
    IMG_SIZE = (224, 224)       # Bilddimensionen in Pixel
    BATCH_SIZE = 32             # Batch Size
    EPOCHS = 30                 # Anzahl Epochen
    VAL_SPLIT = 0.2             # Anteil Validierungsdaten
    RANDOM_SEED = 7             # Reproduzierbarkeit
    LEARNING_RATE = 1e-2        # 👈 Hier kannst du die Lernrate frei wählen
else:
    IMG_SIZE = (int(input("Image height: ")), int(input("Image width: ")))
    BATCH_SIZE = int(input("Batch size: "))
    EPOCHS = int(input("Epochs: "))
    VAL_SPLIT = float(input("Validation Split: "))
    RANDOM_SEED = 7
    LEARNING_RATE = float(input("Learning rate (e.g. 0.001): "))

folder_name = input("Folder name: ")
model_name = str(input("Model name (needs appendix of '.keras'): "))

# ---------------------------
# Daten laden
# ---------------------------
DATA_DIRS = [folder_name]

def load_data():
    X, y = [], []
    total_files = 0
    print("Scanning folders:", DATA_DIRS)
    for folder in DATA_DIRS:
        for file in os.listdir(folder):
            if file.endswith('.png') and 'label' in file:
                total_files += 1
                label = int(file.split('label')[1][0])
                img_path = os.path.join(folder, file)
                img = Image.open(img_path).convert('RGB').resize(IMG_SIZE)
                X.append(np.array(img) / 255.0)   # Normalisierung
                y.append(label)
    print(f"✅ Loaded {len(X)} / {total_files} total images.")
    return np.array(X), np.array(y)

X, y = load_data()

# Shuffle + Split
np.random.seed(RANDOM_SEED)
indices = np.arange(len(X))
np.random.shuffle(indices)
X, y = X[indices], y[indices]

split_index = int(len(X) * (1 - VAL_SPLIT))
X_train, X_val = X[:split_index], X[split_index:]
y_train, y_val = y[:split_index], y[split_index:]

print(f"Training samples: {len(X_train)}")
print(f"Validation samples: {len(X_val)}")

# ---------------------------
# Modell bauen
# ---------------------------
def build_model(img_size, learning_rate):
    model = models.Sequential([
        layers.Input(shape=(*img_size, 3)),
        layers.Conv2D(32, (3, 3), activation='relu'),
        layers.MaxPooling2D(2, 2),
        layers.Conv2D(64, (3, 3), activation='relu'),
        layers.MaxPooling2D(2, 2),
        layers.Conv2D(128, (3, 3), activation='relu'),
        layers.MaxPooling2D(2, 2),
        layers.Flatten(),
        layers.Dense(128, activation='relu'),
        layers.Dense(1, activation='sigmoid')
    ])
    model.compile(
        optimizer=Adam(learning_rate=learning_rate),
        loss='binary_crossentropy',
        metrics=['accuracy']
    )
    return model

model = build_model(IMG_SIZE, LEARNING_RATE)

# ---------------------------
# Callbacks
# ---------------------------
early_stop = tf.keras.callbacks.EarlyStopping(
    monitor='val_loss',
    patience=5,
    restore_best_weights=True
)

# Class weights (optional, kannst du ändern)
class_weights = {0: 1.0, 1: 2.0}

# ---------------------------
# Training
# ---------------------------
history = model.fit(
    X_train, y_train,
    epochs=EPOCHS,
    batch_size=BATCH_SIZE,
    validation_data=(X_val, y_val),
    callbacks=[early_stop],
    class_weight=class_weights
)

# ---------------------------
# Speichern
# ---------------------------
print("--- done ---")
model.save(f"{model_name}")
print(f"✅ Model saved as {model_name}")

# Inspiration von: https://keras.io/examples/
