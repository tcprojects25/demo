import cv2

# Load the pre-trained Haar Cascade face detection model
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')


def detect_faces_from_video():
    cap = cv2.VideoCapture(0)  # Open webcam

    while True:
        ret, frame = cap.read()

        # Convert the frame to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect faces
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        # Draw rectangles around faces
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

        # Show the video with face detection
        cv2.imshow('Face Detection - Video', frame)

        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


def detect_faces_from_image(image_path):
    # Read the image
    img = cv2.imread(image_path)

    # Convert the image to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Detect faces
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    # Draw rectangles around faces
    for (x, y, w, h) in faces:
        cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)

    # Show the image with face detection
    cv2.imshow('Face Detection - Image', img)

    # Wait until a key is pressed to close the window
    cv2.waitKey(0)
    cv2.destroyAllWindows()

# Choose which method to use: Video or Image
choice = input("Choose method: 'video' for webcam feed or 'image' for image file: ").strip().lower()

if choice == 'video':
    detect_faces_from_video()
elif choice == 'image':
    image_path = input("Enter the image path: ").strip()
    detect_faces_from_image(image_path)
else:
    print("Invalid choice! Please enter 'video' or 'image'.")
