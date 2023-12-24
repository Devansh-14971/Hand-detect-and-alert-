import mediapipe as mp
from boltiot import Bolt
import cv2
import conf_1
import requests
import json

mybolt = Bolt(conf_1.Api_key,conf_1.Device_id)

# Detector is a class that creates an instance that analyses an image input in the corresponding functions 
#and uses google's mediapipe to find and report the location of landmarks that are present in a hand
class Detector():
    
    # Will usually recognize two hands and searches with a tracking confidence of 50%
    def __init__(self,det_Confid = 1, Track_Conf = 0.5, maxHands = 2, mode = True):
        self.mode = mode
        self.det_Confid = det_Confid
        self.Track_Conf = Track_Conf
        self.maxHands = maxHands
        self.mpHands = mp.solutions.hands
        self.Hands = self.mpHands.Hands(self.mode,self.maxHands,self.det_Confid,self.Track_Conf)
        self.mpDraw = mp.solutions.drawing_utils
    #mp.solutions.hands is used to search for hands
    #mp.solutions.hands.Hands() is used to instantiate a Hand object

    def Where_H(self, img, draw = True):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.Results = self.Hands.process(imgRGB)
        if self.Results.multi_hand_landmarks:
            for handLMs in self.Results.multi_hand_landmarks:
                if draw:
                    self.mpDraw.draw_landmarks(img, handLMs, self.mpHands.HAND_CONNECTIONS)
        return img
    #Where_H searches and recognizes landmarks in the image that is given
    
    def Pos(self, img, Order = 0, draw = True):
        LMList = []
        if self.Results.multi_hand_landmarks:
            MyHand = self.Results.multi_hand_landmarks[Order]
            h,w,c = img.shape
            for id,lm in enumerate(MyHand.landmark):
                cx,cy = int(lm.x*w), int(lm.y*h)
                LMList.append([id,cx,cy])
                if draw:
                    cv2.circle(img, (cx, cy), 8, (225, 0, 0), -1)
        return LMList
    # Pos returns a list that contains the coordinates of all the Landmarks
    # The Order variable is used to find the latest hand detected
    # LMList stores the id and the current coordinates of all hand Landmarks


#Rect class is used to locate the quadrant in which the tracked finger is found
class Rect():

    def __init__(self, Index: (int), Centre: (int)):
        self.Coor,self.Centre = Index,Centre
        x,y = self.Coor[0],self.Coor[1]
        x1,y1 = Centre[0],Centre[1]
        if(x>x1 and y>y1):
            self.Quad = 1
        elif(y>y1 and x<x1):
            self.Quad = 2
        elif(y<y1 and x<x1):
            self.Quad = 3
        elif(y<y1 and x>x1):
            self.Quad = 4
   
    def Find_Edge(self):
        Shape = (self.Centre[0]*2,self.Centre[1]*2)
        if(self.Quad==1):
            Edge = Shape
        elif(self.Quad==2):
            Edge = (0,Shape[1])
        elif(self.Quad==3):
            Edge = (0,0)
        elif(self.Quad==4):
            Edge = (Shape[0],0)
        return Edge

# send_telegram_msg() sends the desired message through Telegram to the receiver
def send_telegram_msg(message):

    url = "https://api.telegram.org/" + conf_1.telegram_bot_id + "/sendMessage"
    data = {
        "chat_id": conf_1.telegram_chat_id,
        "text": message
    }
    response = requests.request("POST", url, params=data)
    telegram_data = json.loads(response.text)
    if(not telegram_data['ok']):  # This is the step I use to debug the function
        print(telegram_data)

def main():
    W = 0
    Capt = cv2.VideoCapture(0)
    #Capture video
    detect = Detector()
    while True:        
        success,frame = Capt.read()
        #Get one frame as an image        
        frame = detect.Where_H(frame, draw = False)
        #Use Detector.Where_H to get mp.solutions.hands.Hands.process.multi_hand_landmarks
        #This returns all the recognized hand landmarks        
        LML = detect.Pos(frame, draw = False)
        #Use Detector.Pos to get a list of all landmarks found
        h,w,c = frame.shape
        
        if(LML):
            x1, y1 = LML[8][1], LML[8][2]
            if(W==0):
                rect = Rect(Index = (x1,y1),Centre = (w//2,h//2))
                if(rect.Quad==2):
                    
                    cv2.rectangle(frame, (w//2,h//2), rect.Find_Edge(), (100,0,0), -1)  
                    #This flashes a rectangle in the designated section of the screen, bringing attention to the screen                    
                    mybolt.digitalWrite('0','HIGH')
                    #This activates the buzzer once 
                    send_telegram_msg('Something is moving')
                    #This sends a message to the receiver
                    W = 1
                    mybolt.digitalWrite('0','LOW')

        cv2.circle(frame,(x1,y1),10,(0,225,0),-1)
        #You can use cv2.flip(frame,...) to flip the image displayed    
        cv2.imshow("Is_someone_there?", frame)

        k = cv2.waitKey(1) & 0xff
        #This waits for the press of the 'q' key on the keyboard and exits the program once it is pressed
        
        if k == ord('q'):
            break
    #These statements terminate the onscreen dialog-box
    Capt.release()
    cv2.destroyAllWindows()

if __name__=='__main__':
    main()