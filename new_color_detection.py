import cv2
import numpy as np
import imutils

# Fix for Wayland error (add at the very beginning)
import os
os.environ["QT_QPA_PLATFORM"] = "xcb"  # or "wayland" if supported

# Initialize Pi camera using libcamera
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)  # Try V4L2 backend

if not cap.isOpened():
    # Try with different parameters for Pi camera
    print("Trying alternative camera parameters...")
    cap = cv2.VideoCapture(0, cv2.CAP_ANY)
    
if not cap.isOpened():
    print("ERROR: Could not open camera!")
    print("Trying direct camera index 0 with default backend...")
    cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("FATAL: No camera detected!")
    exit(1)

print("Camera opened successfully")

# Set resolution
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
def nothing(x):
    pass

cv2.namedWindow("Trackbars")
cv2.resizeWindow("Trackbars", 400, 300)

# Trackbars for HSV range
cv2.createTrackbar("LH", "Trackbars", 0, 179, nothing)
cv2.createTrackbar("LS", "Trackbars", 0, 255, nothing)
cv2.createTrackbar("LV", "Trackbars", 0, 255, nothing)
cv2.createTrackbar("UH", "Trackbars", 179, 179, nothing)
cv2.createTrackbar("US", "Trackbars", 255, 255, nothing)
cv2.createTrackbar("UV", "Trackbars", 255, 255, nothing)

while True:
        ret,frame= cap.read()
        
        if not ret:
                print("Failed to grab frame!")
                continue
        
        if frame is None:
                print("Frame is None!")
                continue

        if frame.size and frame.size == 0:
                print("Empty frame!")
                continue

        print(f"frame shape: {frame.shape}, frame type: {frame.dtype}")

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        hsv = cv2.cvtColor(frame,cv2.COLOR_BGR2HSV)

               # Range for lower
        lower_red = np.array([0,50,50])
        upper_red = np.array([10,255,255])
        mask1 = cv2.inRange(hsv, lower_red, upper_red)

        lower_orange = np.array([11,100,100])
        upper_orange = np.array([25,255,255])
        mask3 = cv2.inRange(hsv, lower_orange, upper_orange)

        lower_yellow = np.array([26,100,100])
        upper_yellow = np.array([35,255,255])
        mask5 = cv2.inRange(hsv, lower_yellow, upper_yellow)
        
        lower_green = np.array([36,50,50])
        upper_green = np.array([85,255,255])
        mask7 = cv2.inRange(hsv, lower_green, upper_green)

        lower_light_blue = np.array([86,50,50])
        upper_light_blue = np.array([100,255,255])
        mask11 = cv2.inRange(hsv, lower_light_blue, upper_light_blue)

        lower_blue = np.array([101,50,50])
        upper_blue = np.array([130,255,255])
        mask13 = cv2.inRange(hsv, lower_blue, upper_blue)

        lower_violet = np.array([131,50,50])
        upper_violet = np.array([145,255,255])
        mask15 = cv2.inRange(hsv, lower_violet, upper_violet)

        lower_purple = np.array([146,50,50])
        upper_purple = np.array([160,255,255])
        mask17 = cv2.inRange(hsv, lower_purple, upper_purple)

        lower_pink = np.array([161,50,50])
        upper_pink = np.array([169,255,255])
        mask19 = cv2.inRange(hsv, lower_pink, upper_pink)

        lower_gray = np.array([0,0,40])
        upper_gray = np.array([180,18,230])
        mask21 = cv2.inRange(hsv, lower_gray, upper_gray)
         
        lower_black = np.array([0,0,0])
        upper_black = np.array([180,255,50])
        mask23 = cv2.inRange(hsv, lower_black, upper_black)
 
        lower_white = np.array([0,0,200])
        upper_white = np.array([180,30,255])
        mask25 = cv2.inRange(hsv, lower_white, upper_white)

        lower_brown = np.array([10,100,20])
        upper_brown = np.array([20,255,200])
        mask27 = cv2.inRange(hsv, lower_brown, upper_brown)

        lower_beige = np.array([5,20,130])
        upper_beige = np.array([30,120,255])
        mask29 = cv2.inRange(hsv, lower_beige, upper_beige)


        # Range for upper range
        lower_red = np.array([170,50,50])
        upper_red = np.array([180,255,255])
        mask2 = cv2.inRange(hsv, lower_red, upper_red)

        lower_orange = np.array([11,100,100])
        upper_orange = np.array([25,255,255])
        mask4 = cv2.inRange(hsv, lower_orange, upper_orange)

        lower_yellow = np.array([26,100,100])
        upper_yellow = np.array([35,255,255])
        mask6 = cv2.inRange(hsv, lower_yellow, upper_yellow)

        lower_green = np.array([36,50,50])
        upper_green = np.array([85,255,255])
        mask8 = cv2.inRange(hsv, lower_green, upper_green)

        lower_light_blue = np.array([86,50,50])
        upper_light_blue = np.array([100,255,255])
        mask12 = cv2.inRange(hsv, lower_light_blue, upper_light_blue)

        lower_blue = np.array([101,50,50])
        upper_blue = np.array([130,255,255])
        mask14 = cv2.inRange(hsv, lower_blue, upper_blue)

        lower_violet = np.array([131,50,50])
        upper_violet = np.array([145,255,255])
        mask16 = cv2.inRange(hsv, lower_violet, upper_violet)

        lower_purple = np.array([146,50,50])
        upper_purple = np.array([160,255,255])
        mask18 = cv2.inRange(hsv, lower_purple, upper_purple)

        lower_pink = np.array([161,50,50])
        upper_pink = np.array([169,255,255])
        mask20 = cv2.inRange(hsv, lower_pink, upper_pink)

        lower_gray = np.array([0,0,40])
        upper_gray = np.array([180,18,230])
        mask22 = cv2.inRange(hsv, lower_gray, upper_gray)
        
        lower_black = np.array([0,0,0])
        upper_black = np.array([180,255,50])
        mask24 = cv2.inRange(hsv, lower_black, upper_black)

        lower_white = np.array([0,0,200])
        upper_white = np.array([180,30,255])
        mask26 = cv2.inRange(hsv, lower_white, upper_white)

        lower_brown = np.array([10,50,50])
        upper_brown = np.array([25,255,200])
        mask28 = cv2.inRange(hsv, lower_brown, upper_brown)
        
        lower_beige = np.array([5,20,130])
        upper_beige = np.array([30,120,255])
        mask30 = cv2.inRange(hsv, lower_beige, upper_beige)

        # Generating the final mask to detect color
        mask1 = mask1+mask2
        mask3 = mask3+mask4
        mask5 = mask5+mask6
        mask7 = mask7+mask8
        mask11 = mask11+mask12
        mask13 = mask13+mask14
        mask15 = mask15+mask16
        mask17 = mask17+mask18
        mask19 = mask19+mask20
        mask21 = mask21+mask22
        mask23=mask23
        mask25=mask25
        mask27=mask27+mask28
        mask29=mask29+mask30
        borderc1=cv2.findContours(mask1, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        borderc1=imutils.grab_contours(borderc1)

        borderc2=cv2.findContours(mask3, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        borderc2=imutils.grab_contours(borderc2)

        borderc3=cv2.findContours(mask5, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        borderc3=imutils.grab_contours(borderc3)

        borderc4=cv2.findContours(mask7, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        borderc4=imutils.grab_contours(borderc4)

        borderc6=cv2.findContours(mask11, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        borderc6=imutils.grab_contours(borderc6)

        borderc7=cv2.findContours(mask13, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        borderc7=imutils.grab_contours(borderc7)

        borderc8=cv2.findContours(mask15, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        borderc8=imutils.grab_contours(borderc8)

        borderc9=cv2.findContours(mask17, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        borderc9=imutils.grab_contours(borderc9)

        borderc10=cv2.findContours(mask19, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        borderc10=imutils.grab_contours(borderc10)

        borderc11=cv2.findContours(mask21, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        borderc11=imutils.grab_contours(borderc11)

        borderc12=cv2.findContours(mask23, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        borderc12=imutils.grab_contours(borderc12)

        borderc13=cv2.findContours(mask25, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        borderc13=imutils.grab_contours(borderc13)

        borderc14=cv2.findContours(mask27, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        borderc14=imutils.grab_contours(borderc14)

        borderc15=cv2.findContours(mask27, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        borderc15=imutils.grab_contours(borderc15)

        for a in borderc1:
                Carea = cv2.contourArea(a)
                if Carea > 1500:
                    cv2.drawContours(frame,[a],-1,(0,255,0), 1)
                    centroid = cv2.moments(a)
                    cx = int(centroid["m10"]/ centroid["m00"])
                    cy = int(centroid["m01"]/ centroid["m00"])
                    cv2.circle(frame,(cx,cy),1,(0,0,0),0)
                    cv2.putText(frame, "Red", (cx-10, cy-5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255))

        for a in borderc2:
                Carea = cv2.contourArea(a)
                if Carea > 1500:
                    cv2.drawContours(frame,[a],-1,(0,255,0), 1)
                    centroid = cv2.moments(a)
                    cx = int(centroid["m10"]/ centroid["m00"])
                    cy = int(centroid["m01"]/ centroid["m00"])
                    cv2.circle(frame,(cx,cy),1,(0,0,0),0)
                    cv2.putText(frame, "Orange", (cx-20, cy-10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255))


        for a in borderc3:
                Carea = cv2.contourArea(a)
                if Carea > 1500:
                    cv2.drawContours(frame,[a],-1,(0,255,0), 1)
                    centroid = cv2.moments(a)
                    cx = int(centroid["m10"]/ centroid["m00"])
                    cy = int(centroid["m01"]/ centroid["m00"])
                    cv2.circle(frame,(cx,cy),1,(0,0,0),0)
                    cv2.putText(frame, "Yellow", (cx-10, cy-10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255))


        for a in borderc4:
                Carea = cv2.contourArea(a)
                if Carea > 1500:
                    cv2.drawContours(frame,[a],-1,(0,255,0), 1)
                    centroid = cv2.moments(a)
                    cx = int(centroid["m10"]/ centroid["m00"])
                    cy = int(centroid["m01"]/ centroid["m00"])
                    cv2.circle(frame,(cx,cy),1,(0,0,0),0)
                    cv2.putText(frame, "Green", (cx-10, cy-10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255))


        for a in borderc6:
                Carea = cv2.contourArea(a)
                if Carea > 1500:
                    cv2.drawContours(frame,[a],-1,(0,255,0), 1)
                    centroid = cv2.moments(a)
                    cx = int(centroid["m10"]/ centroid["m00"])
                    cy = int(centroid["m01"]/ centroid["m00"])
                    cv2.circle(frame,(cx,cy),1,(0,0,0),0)
                    cv2.putText(frame, "Light Blue", (cx-10, cy-10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255))


        for a in borderc7:
                Carea = cv2.contourArea(a)
                if Carea > 1500:
                    cv2.drawContours(frame,[a],-1,(0,255,0), 1)
                    centroid = cv2.moments(a)
                    cx = int(centroid["m10"]/ centroid["m00"])
                    cy = int(centroid["m01"]/ centroid["m00"])
                    cv2.circle(frame,(cx,cy),1,(0,0,0),0)
                    cv2.putText(frame, "Blue", (cx-10, cy-10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255))


        for a in borderc8:
                Carea = cv2.contourArea(a)
                if Carea > 1500:
                    cv2.drawContours(frame,[a],-1,(0,255,0), 1)
                    centroid = cv2.moments(a)
                    cx = int(centroid["m10"]/ centroid["m00"])
                    cy = int(centroid["m01"]/ centroid["m00"])
                    cv2.circle(frame,(cx,cy),1,(0,0,0),0)
                    cv2.putText(frame, "Violet", (cx-10, cy-10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255))


        for a in borderc9:
                Carea = cv2.contourArea(a)
                if Carea > 1500:
                    cv2.drawContours(frame,[a],-1,(0,255,0), 1)
                    centroid = cv2.moments(a)
                    cx = int(centroid["m10"]/ centroid["m00"])
                    cy = int(centroid["m01"]/ centroid["m00"])
                    cv2.circle(frame,(cx,cy),1,(0,0,0),0)
                    cv2.putText(frame, "Purple", (cx-10, cy-1), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255))


        for a in borderc10:
                Carea = cv2.contourArea(a)
                if Carea > 1500:
                    cv2.drawContours(frame,[a],-1,(0,255,0), 1)
                    centroid = cv2.moments(a)
                    cx = int(centroid["m10"]/ centroid["m00"])
                    cy = int(centroid["m01"]/ centroid["m00"])
                    cv2.circle(frame,(cx,cy),1,(0,0,0),0)
                    cv2.putText(frame, "Pink", (cx-10, cy-10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255))


        for a in borderc11:
                Carea = cv2.contourArea(a)
                if Carea > 1500:
                    b=cv2.drawContours(frame,[a],-1,(0,255,0), 1)
                    centroid = cv2.moments(a)
                    cx = int(centroid["m10"]/ centroid["m00"])
                    cy = int(centroid["m01"]/ centroid["m00"])
                    cv2.circle(frame,(cx,cy),1,(0,0,0),0)
                    cv2.putText(frame, "Gray", (cx-10, cy-10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255))

        for a in borderc12:
               Carea = cv2.contourArea(a)
               if Carea > 1500:
                    b = cv2.drawContours(frame, [a], -1, (0,255,0), 1)
                    centroid = cv2.moments(a)
                    cx = int(centroid["m10"] / centroid["m00"])
                    cy = int(centroid["m01"] / centroid["m00"])
                    cv2.circle(frame, (cx, cy), 1, (0,0,0), 0)
                    cv2.putText(frame, "Black", (cx-10, cy-10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255))  

        for a in borderc13:
                Carea = cv2.contourArea(a)
                if Carea > 1500:
                     b = cv2.drawContours(frame, [a], -1, (0,255,0), 1)
                     centroid = cv2.moments(a)
                     cx = int(centroid["m10"] / centroid["m00"])
                     cy = int(centroid["m01"] / centroid["m00"])
                     cv2.circle(frame, (cx, cy), 1, (0,0,0), 0)
                     cv2.putText(frame, "White", (cx-10, cy-10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255)) 

        for a in borderc14:
                Carea = cv2.contourArea(a)
                if Carea > 1500:
                    b= cv2.drawContours(frame, [a], -1, (19, 69, 139), 2)  # Brownish outline
                    centroid = cv2.moments(a)
                    cx = int(centroid["m10"] / centroid["m00"])
                    cy = int(centroid["m01"] / centroid["m00"])
                    cv2.circle(frame, (cx, cy), 1, (0,0,0), 0)
                    cv2.putText(frame, "Brwon", (cx-10, cy-10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255))

        for a in borderc15:
                Carea = cv2.contourArea(a)
                if Carea > 1500:
                    b= cv2.drawContours(frame, [a], -1, (19, 69, 139), 2)  # Brownish outline
                    centroid = cv2.moments(a)
                    cx = int(centroid["m10"] / centroid["m00"])
                    cy = int(centroid["m01"] / centroid["m00"])
                    cv2.circle(frame, (cx, cy), 1, (0,0,0), 0)
                    cv2.putText(frame, "Beige", (cx-10, cy-10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255))
        if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cv2.imshow("result",frame)            
        if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cv2.imshow("result",frame)
        
cap.release()
cv2.destroyAllWindows()