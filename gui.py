from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import tkinter as tk
from tkinter import filedialog
import cv2
import os
import shutil
import csv
from datetime import datetime
from PIL import Image, ImageTk

selected_file = None
def generate_new_id():
    try:
        with open("criminals.csv", "r") as f:
            reader = csv.reader(f)
            rows = list(reader)

            if len(rows) <= 1:
                return "C001"

            last_id = rows[-1][0]
            number = int(last_id[1:])
            new_id = number + 1

            return f"C{new_id:03d}"

    except:
        return "C001"

def preprocess(path):
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return None
    img = cv2.resize(img, (300, 300))
    img = cv2.equalizeHist(img)
    img = cv2.GaussianBlur(img, (5, 5), 0)
    return img

def get_similarity(img1, img2):
    orb = cv2.ORB_create(nfeatures=1000)
    kp1, des1 = orb.detectAndCompute(img1, None)
    kp2, des2 = orb.detectAndCompute(img2, None)

    if des1 is None or des2 is None:
        return 0

    matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = matcher.match(des1, des2)

    if len(matches) == 0:
        return 0

    good_matches = [m for m in matches if m.distance < 50]
    return (len(good_matches) / len(matches)) * 100

def get_criminal_info(fingerprint_name):
    if not os.path.exists("criminals.csv"):
        return None

    with open("criminals.csv", "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["Image"] == fingerprint_name:
                return row

    return None

def load_fingerprint():
    global selected_file

    selected_file = filedialog.askopenfilename(
        title="Select Fingerprint Image",
        filetypes=[("Image Files", "*.bmp *.png *.jpg *.jpeg")]
    )

    if selected_file:
        status_label.config(text=f"Loaded: {os.path.basename(selected_file)}")

def search_database():
    if selected_file is None:
        status_label.config(text="Please load fingerprint first")
        return

    unknown_img = preprocess(selected_file)
    database_folder = "database"

    best_score = 0
    best_match = None

    for filename in os.listdir(database_folder):
        if filename.lower().endswith((".bmp", ".png", ".jpg", ".jpeg")):
            file_path = os.path.join(database_folder, filename)
            db_img = preprocess(file_path)

            if db_img is None:
                continue

            similarity = get_similarity(unknown_img, db_img)

            if similarity > best_score:
                best_score = similarity
                best_match = filename

    if best_score > 15:
        result = "MATCH FOUND"
    else:
        result = "NO MATCH FOUND"

    criminal = get_criminal_info(best_match)

    if criminal:
        status_text = (
            f"Best Match: {best_match}\n"
            f"ID: {criminal['ID']}\n"
            f"Name: {criminal['Name']}\n"
            f"Crime: {criminal['Crime']}\n"
            f"Similarity: {best_score:.2f}%\n"
            f"Result: {result}"
        )
    else:
        status_text = (
            f"Best Match: {best_match}\n"
            f"Similarity: {best_score:.2f}%\n"
            f"Result: {result}"
        )

    history_file = "match_history.csv"
    file_exists = os.path.exists(history_file)

    with open(history_file, "a", newline="") as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow(["Date", "Unknown File", "Best Match", "Similarity", "Result"])

        writer.writerow([
            datetime.now(),
            os.path.basename(selected_file),
            best_match,
            f"{best_score:.2f}%",
            result
        ])

    status_label.config(text=status_text)

    if best_match is not None:
        matched_path = os.path.join(database_folder, best_match)

        unknown_display = Image.open(selected_file).resize((150, 150))
        matched_display = Image.open(matched_path).resize((150, 150))

        combined = Image.new("RGB", (300, 150))
        combined.paste(unknown_display, (0, 0))
        combined.paste(matched_display, (150, 0))

        img_tk = ImageTk.PhotoImage(combined)
        image_label.config(image=img_tk)
        image_label.image = img_tk

def enroll_fingerprint():
    if selected_file is None:
        status_label.config(text="Load fingerprint first to enroll")
        return

    database_folder = "database"

    if not os.path.exists(database_folder):
        os.makedirs(database_folder)

    filename = os.path.basename(selected_file)
    destination = os.path.join(database_folder, filename)

    shutil.copy(selected_file, destination)

    status_label.config(text=f"Enrolled: {filename}")
def add_criminal_record():

    def save_record():

        cid = generate_new_id()
        name = name_entry.get()
        crime = crime_entry.get()

        if selected_file is None:
            status_label.config(text="Load fingerprint first")
            return

        image_name = os.path.basename(selected_file)

        file_exists = os.path.exists("criminals.csv")

        with open("criminals.csv", "a", newline="") as file:

            writer = csv.writer(file)

            if not file_exists:
                writer.writerow(["ID", "Name", "Crime", "Image"])

            writer.writerow([
                cid,
                name,
                crime,
                image_name
            ])

        status_label.config(text=f"Criminal {name} added")

        form.destroy()

    form = tk.Toplevel(root)
    form.title("Add Criminal Record")
    form.geometry("300x250")

    tk.Label(form, text="Criminal ID").pack()
    id_entry = tk.Entry(form)
    id_entry.pack()

    tk.Label(form, text="Name").pack()
    name_entry = tk.Entry(form)
    name_entry.pack()

    tk.Label(form, text="Crime").pack()
    crime_entry = tk.Entry(form)
    crime_entry.pack()

    tk.Button(form, text="Save Record", command=save_record).pack(pady=10)
def capture_fingerprint():
    global selected_file

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        status_label.config(text="Camera not found")
        return

    while True:
        ret, frame = cap.read()

        if not ret:
            status_label.config(text="Failed to read camera")
            break

        cv2.imshow("Press SPACE to capture, ESC to cancel", frame)

        key = cv2.waitKey(1)

        if key == 27:  # ESC
            break

        if key == 32:  # SPACE
            capture_path = "data/captured_fingerprint.jpg"
            cv2.imwrite(capture_path, frame)
            selected_file = capture_path
            status_label.config(text="Fingerprint captured successfully")
            break

    cap.release()
    cv2.destroyAllWindows()
def cnn_predict():
    global selected_file

    if selected_file is None:
        status_label.config(text="Load fingerprint first")
        return

    import torch
    import torch.nn as nn
    from torchvision import transforms
    from PIL import Image

    # CNN Model
    class FingerprintCNN(nn.Module):
        def __init__(self, num_classes):
            super(FingerprintCNN, self).__init__()

            self.model = nn.Sequential(
                nn.Conv2d(1, 16, 3, padding=1),
                nn.ReLU(),
                nn.MaxPool2d(2),

                nn.Conv2d(16, 32, 3, padding=1),
                nn.ReLU(),
                nn.MaxPool2d(2),

                nn.Flatten(),
                nn.Linear(32 * 32 * 32, 128),
                nn.ReLU(),
                nn.Linear(128, num_classes)
            )

        def forward(self, x):
            return self.model(x)

    # Classes (same as training)
    classes = ['person1', 'person2', 'person3']

    model = FingerprintCNN(len(classes))
    model.load_state_dict(torch.load("fingerprint_cnn.pth"))
    model.eval()

    transform = transforms.Compose([
        transforms.Grayscale(num_output_channels=1),
        transforms.Resize((128,128)),
        transforms.ToTensor()
    ])

    image = Image.open(selected_file)
    image = transform(image).unsqueeze(0)

    with torch.no_grad():
        outputs = model(image)
        probabilities = torch.softmax(outputs, dim=1)
        confidence, predicted = torch.max(probabilities, 1)

    predicted_class = classes[predicted.item()]
    confidence_score = confidence.item() * 100

    status_label.config(
    text=f"CNN Prediction: {predicted_class}\nConfidence: {confidence_score:.2f}%"
)
def hybrid_recognition():
    global selected_file

    if selected_file is None:
        status_label.config(text="Load fingerprint first")
        return

    import torch
    import torch.nn as nn
    from torchvision import transforms
    from PIL import Image

    # ---------------- ORB MATCH ----------------

    unknown_img = preprocess(selected_file)
    database_folder = "database"

    best_score = 0
    best_match = None

    for filename in os.listdir(database_folder):

        if filename.lower().endswith((".bmp",".png",".jpg",".jpeg")):

            file_path = os.path.join(database_folder, filename)
            db_img = preprocess(file_path)

            if db_img is None:
                continue

            similarity = get_similarity(
                unknown_img,
                db_img
            )

            if similarity > best_score:
                best_score = similarity
                best_match = filename

    # ---------------- CNN MODEL ----------------

    class FingerprintCNN(nn.Module):
        def __init__(self, num_classes):
            super(FingerprintCNN, self).__init__()

            self.model = nn.Sequential(
                nn.Conv2d(1,16,3,padding=1),
                nn.ReLU(),
                nn.MaxPool2d(2),

                nn.Conv2d(16,32,3,padding=1),
                nn.ReLU(),
                nn.MaxPool2d(2),

                nn.Flatten(),
                nn.Linear(32*32*32,128),
                nn.ReLU(),
                nn.Linear(128,num_classes)
            )

        def forward(self,x):
            return self.model(x)

    classes = ['person1','person2','person3']

    model = FingerprintCNN(len(classes))
    model.load_state_dict(
        torch.load("fingerprint_cnn.pth")
    )
    model.eval()

    transform = transforms.Compose([
        transforms.Grayscale(1),
        transforms.Resize((128,128)),
        transforms.ToTensor()
    ])

    image = Image.open(selected_file)
    image = transform(image).unsqueeze(0)

    with torch.no_grad():

        outputs = model(image)
        probabilities = torch.softmax(outputs, dim=1)

        confidence, predicted = torch.max(
            probabilities,
            1
        )

    predicted_class = classes[predicted.item()]
    cnn_confidence = confidence.item() * 100

    # ---------------- FINAL DECISION ----------------

    if best_score > 15 and cnn_confidence > 70:
        final_result = "STRONG MATCH"
    elif best_score > 15:
        final_result = "POSSIBLE MATCH"
    else:
        final_result = "NO MATCH"

    # ---------------- DISPLAY ----------------

    status_label.config(

        text=
        f"ORB Match: {best_match}\n"
        f"ORB Similarity: {best_score:.2f}%\n\n"
        f"CNN Prediction: {predicted_class}\n"
        f"CNN Confidence: {cnn_confidence:.2f}%\n\n"
        f"Final Decision: {final_result}"
    )
def export_pdf_report():
    global selected_file

    if selected_file is None:
        status_label.config(text="Load fingerprint first")
        return

    unknown_img = preprocess(selected_file)
    database_folder = "database"

    best_score = 0
    best_match = None

    for filename in os.listdir(database_folder):
        if filename.lower().endswith((".bmp", ".png", ".jpg", ".jpeg")):
            file_path = os.path.join(database_folder, filename)
            db_img = preprocess(file_path)

            if db_img is None:
                continue

            similarity = get_similarity(unknown_img, db_img)

            if similarity > best_score:
                best_score = similarity
                best_match = filename

    criminal = get_criminal_info(best_match)

    if best_score > 15:
        result = "MATCH FOUND"
    else:
        result = "NO MATCH FOUND"

    report_name = "fingerprint_report.pdf"

    pdf = canvas.Canvas(report_name, pagesize=A4)
    width, height = A4

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(170, height - 60, "Fingerprint Match Report")

    pdf.setFont("Helvetica", 12)
    y = height - 110

    pdf.drawString(50, y, f"Date/Time: {datetime.now()}")
    y -= 30

    pdf.drawString(50, y, f"Unknown Fingerprint: {os.path.basename(selected_file)}")
    y -= 25

    pdf.drawString(50, y, f"Best Match: {best_match}")
    y -= 25

    pdf.drawString(50, y, f"ORB Similarity: {best_score:.2f}%")
    y -= 25

    pdf.drawString(50, y, f"Final Result: {result}")
    y -= 40

    if criminal:
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, y, "Criminal Record")
        y -= 30

        pdf.setFont("Helvetica", 12)
        pdf.drawString(50, y, f"Criminal ID: {criminal['ID']}")
        y -= 25

        pdf.drawString(50, y, f"Name: {criminal['Name']}")
        y -= 25

        pdf.drawString(50, y, f"Crime: {criminal['Crime']}")
        y -= 25

        pdf.drawString(50, y, f"Fingerprint Image: {criminal['Image']}")

    pdf.save()

    status_label.config(text=f"PDF report saved: {report_name}")
def show_dashboard():

    total_criminals = 0
    total_searches = 0
    matches_found = 0
    no_matches = 0

    # Count criminals
    if os.path.exists("criminals.csv"):

        with open("criminals.csv", "r") as file:
            reader = csv.reader(file)
            rows = list(reader)

            total_criminals = len(rows) - 1

    # Count search history
    if os.path.exists("match_history.csv"):

        with open("match_history.csv", "r") as file:
            reader = csv.DictReader(file)

            for row in reader:

                total_searches += 1

                if "MATCH" in row["Result"]:
                    matches_found += 1
                else:
                    no_matches += 1

    dashboard = tk.Toplevel(root)
    dashboard.title("System Dashboard")
    dashboard.geometry("300x250")

    tk.Label(
        dashboard,
        text="Fingerprint System Dashboard",
        font=("Arial", 12, "bold")
    ).pack(pady=10)

    tk.Label(
        dashboard,
        text=f"Total Criminals: {total_criminals}"
    ).pack(pady=5)

    tk.Label(
        dashboard,
        text=f"Total Searches: {total_searches}"
    ).pack(pady=5)

    tk.Label(
        dashboard,
        text=f"Matches Found: {matches_found}"
    ).pack(pady=5)

    tk.Label(
        dashboard,
        text=f"No Matches: {no_matches}"
    ).pack(pady=5)
def live_recognition():

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        status_label.config(text="Camera not found")
        return

    while True:

        ret, frame = cap.read()

        if not ret:
            break

        cv2.imshow(
            "LIVE Recognition - Press S to Search | ESC to Exit",
            frame
        )

        key = cv2.waitKey(1)

        # ESC → Exit
        if key == 27:
            break

        # S → Search current frame
        if key == ord('s'):

            temp_path = "live_capture.jpg"

            cv2.imwrite(temp_path, frame)

            global selected_file
            selected_file = temp_path

            hybrid_recognition()

    cap.release()
    cv2.destroyAllWindows()
root = tk.Tk()
root.title("Fingerprint Recognition System")
root.geometry("500x550")

title_label = tk.Label(root, text="Fingerprint Recognition System", font=("Arial", 14, "bold"))
title_label.pack(pady=10)

tk.Button(root, text="Load Fingerprint", width=25, command=load_fingerprint).pack(pady=5)
tk.Button(root, text="Capture From Webcam", width=25, command=capture_fingerprint).pack(pady=5)
tk.Button(root, text="Search Database", width=25, command=search_database).pack(pady=5)
tk.Button(
    root,
    text="Deep Learning Predict",
    width=25,
    command=cnn_predict
).pack(pady=5)
tk.Button(
    root,
    text="Hybrid Recognition",
    width=25,
    command=hybrid_recognition
).pack(pady=5)
tk.Button(
    root,
    text="Export PDF Report",
    width=25,
    command=export_pdf_report
).pack(pady=5)
tk.Button(
    root,
    text="View Dashboard",
    width=25,
    command=show_dashboard
).pack(pady=5)
tk.Button(
    root,
    text="Live Recognition",
    width=25,
    command=live_recognition
).pack(pady=5)
tk.Button(root, text="Enroll Fingerprint", width=25, command=enroll_fingerprint).pack(pady=5)
tk.Button(root, text="Add Criminal Record", width=25, command=add_criminal_record).pack(pady=5)
tk.Button(root, text="Exit", width=25, command=root.quit).pack(pady=5)

status_label = tk.Label(root, text="Status: Waiting...", fg="blue", justify="center")
status_label.pack(pady=10)

image_label = tk.Label(root)
image_label.pack(pady=10)

root.mainloop()