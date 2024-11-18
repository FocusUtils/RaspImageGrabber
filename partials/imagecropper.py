import rawpy
import cv2
from tkinter import filedialog

def load_image(path):
    ## check file type for raw or not
    file_extention = path.split(".")[-1].lower()
    if file_extention in ["raw", "dng", "nef"]:
        ## load file using rawpy
        raw = rawpy.imread(path)
        img = raw.postprocess()
    else:
        img = cv2.imread(path)
    return img

global x1, y1, x2, y2
x1 = y1 = x2 = y2 = None
def mouse_click(event, x, y,  
                flags, param):
    global x1, y1, x2, y2
    if event == cv2.EVENT_LBUTTONDOWN:
        if x1 == None:
            x1 = x
            y1 = y
        else:
            x2 = x
            y2 = y
        


def ask_for_imgs():
    return filedialog.askopenfilenames()

def get_crop_coords(file_paths):
    if len(file_paths) == 0:
        return []
    
    img = load_image(file_paths[len(file_paths)//2])
    ## crop image
    cv2.imshow("img", img)
    
    cv2.setMouseCallback('img', mouse_click) 
    while True:
        cv2.waitKey(100)
        if x2 != None:
            break
    print(x1, y1, x2, y2)
    cv2.destroyAllWindows()


def crop(path):
    img = load_image(path)
    ## crop image
    img = img[y1:y2, x1:x2]
    return img



if __name__ == "__main__":
    file_paths = ask_for_imgs()
    get_crop_coords(file_paths)
    for path in file_paths:
        img = crop(path)
        cv2.imwrite(".".join(path.split(".")[:-1]) + ".cropped.png", img)
        
        