from flask import Flask, Response
import cv2

app = Flask(__name__)

rtsp_url = "rtsp://admin:a1234567@192.168.100.31:554/cam/realmonitor?channel=1&subtype=0"
cap = cv2.VideoCapture(rtsp_url)

def generate():
    while True:
        success, frame = cap.read()
        if not success:
            break
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    return '<h1>Kamera</h1><img src="/video_feed" width="100%">'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
