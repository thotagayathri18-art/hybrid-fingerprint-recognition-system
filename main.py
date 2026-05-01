import cv2
import os

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

    good_matches = [m for m in matches if m.distance < 50]

    if len(matches) == 0:
        return 0

    similarity = (len(good_matches) / len(matches)) * 100

    return similarity

# Load unknown fingerprint
unknown_path = "data/sample1.bmp"
unknown_img = preprocess(unknown_path)

database_folder = "database"

best_score = 0
best_match = None

for filename in os.listdir(database_folder):

    if filename.lower().endswith((".bmp", ".png", ".jpg", ".jpeg")):

        file_path = os.path.join(database_folder, filename)

        db_img = preprocess(file_path)

        similarity = get_similarity(unknown_img, db_img)

        print(f"{filename} → Similarity: {similarity:.2f}%")

        if similarity > best_score:
            best_score = similarity
            best_match = filename

print("\nBest Match Found:")
print("Fingerprint:", best_match)
print("Similarity:", f"{best_score:.2f}%")

from datetime import datetime

# Decision logic
if best_score > 15:
    print("Result: MATCH FOUND")
    decision = "MATCH"
else:
    print("Result: NO MATCH FOUND")
    decision = "NO MATCH"

# Generate report
report_file = "match_report.txt"

with open(report_file, "w") as file:

    file.write("Fingerprint Match Report\n")
    file.write("------------------------\n")

    file.write(f"Unknown File: {unknown_path}\n")
    file.write(f"Best Match: {best_match}\n")
    file.write(f"Similarity: {best_score:.2f}%\n")

    file.write(f"Decision: {decision}\n")

    file.write(f"Date: {datetime.now()}\n")

print("Report saved as:", report_file)

# Show best match visually
if best_match is not None:

    matched_path = os.path.join(database_folder, best_match)

    matched_img = preprocess(matched_path)

    combined = cv2.hconcat([unknown_img, matched_img])

    cv2.imshow("Unknown vs Best Match", combined)
    cv2.waitKey(0)
    cv2.destroyAllWindows()