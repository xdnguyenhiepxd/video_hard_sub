import pytesseract
import cv2
from collections import Counter
import string
from difflib import SequenceMatcher
import multiprocessing as np
from functools import partial
import numpy as num
from pytube import YouTube

#Truyền link video cần lấy sub
link = "https://www.youtube.com/watch?v=fb9KXo2y06A"

# --------------------------- Bắt đầu lấy thông tin video --------------------------- 
yt = YouTube(link).streams.filter(res ="720p")[0].download(output_path=r'/home/amnhacsaigon/hoanchu/gen_text_in_img/video')

#  --------------------------- Bắt đầu phân tích --------------------------- 
# Tạo file vật lý lưu vào server
os.rename(yt,"/home/amnhacsaigon/hoanchu/gen_text_in_img/video/a.mp4")
os.system("ffmpeg -y -i /home/amnhacsaigon/hoanchu/gen_text_in_img/video/a.mp4 -r 5 /home/amnhacsaigon/hoanchu/gen_text_in_img/video/a_a.mp4")


"""
    - Tạo hàm get text để thực hiện lấy text của 1 frame
"""
def get_text(frame,lang):
    second_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    a = num.count_nonzero(second_gray > 127)
    b = num.count_nonzero(second_gray <127)
    if a >= b:
        thre = 115
    else:
        thre = 240
    mask = cv2.threshold(second_gray, thre, 255, cv2.THRESH_BINARY)[1]
    mask = 255 - mask
    kernel = num.ones((1,1), num.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    text = pytesseract.image_to_string(mask,lang=lang).replace("\n"," ")
    return text

"""
    - Hàm get text in img sẽ thực hiện:
        + Đọc video lưu từng frame vào list_frame.
        + Sử dụng Pool để chạy đa luồng
        + Sau khi chạy xong đa luồng tất cả các text của video sẽ lưu lại vào list_text
        + Khi có list_text thì sẽ tiến hành tính thời gian và lấy text chính xác nhất rồi lưu vào biến sub
"""
    
def get_text_in_img(link_video,lang,x,y,width,height,time_down):
    video_capture = cv2.VideoCapture(link_video)
    fps = int(video_capture.get(cv2.CAP_PROP_FPS))
    print(fps)
    print(str(int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))))
    print("link_video",link_video)
    count = 0
    check = 1
    config = '/home/amnhacsaigon/hoanchu/gen_text_in_img/tessdata'
    sub = ""
    stt = 1
    soluongf = -1
    text = ""
    list_t = []
    list_sub = []
    list_time_start = []
    list_time_end = []
    list_frame = []
    for sof in range(int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))):

        ret, frame= video_capture.read()
        
        try:
            frame = frame[y:y+height,x:x+width]
            list_frame.append(frame)
        except:
            pass
    
    p = np.Pool()
    list_text = p.map(partial(get_text, lang=lang), list_frame)
    p.close()
    p.terminate()
    for text in list_text:
"""
    - Check==1 kiểm tra xem frame đầu tiên có text hay không?. Nếu có text thì sẽ lấy ra thời gian bắt đầu
"""
        
        if check == 1:
            if text !="":
                check =2
                cout =count - time_down*fps
                f=cout%fps/fps
                f=str(cout%fps/fps)
                f = f[:5].split(".")
                f = f[-1]
                if len(f) == 1:
                    f = f +"00"
                if len(f) == 2:
                    f = f +"0"
                second = int(cout/fps - 60*int(cout/(fps*60)))
                if second < 0:
                    second = 0
                time_start = '{h:02d}:{m:02d}:{s:02d},{f}'.format(h = int(cout/(fps*60*60)),m=int(cout/(fps*60)),s=second,f = str(f))

"""
    - Check==2 sẽ lấy ra text có số lượng nhiều nhất trong list bằng cách sử dụng hàm Counter, kiểm tra <0.6 để lấy ra những
               trường hợp có 2 câu khi tốc độ chuyển frame nhanh
"""
        if check == 2:
            if soluongf < 0:
                print(1)
                if text != "":
                    list_t.append(text)
                    if len(list_t)> 1:
                        if SequenceMatcher(None, text.lower(), list_t[-2].lower()).ratio() < 0.6:
                            list_count = Counter(list_t)

                            sub_text = max(list_count, key = list_count.get)
                            check = 3
            soluongf -= 1
        
        
"""
    - Check==3 khi chạy xong check == 2 thì sẽ chạy tới hàm check == 3 để lấy ra thời gian kết thúc của câu. 
"""        
        
        if check == 3:
            cout =count - time_down*fps
            f=cout%fps/fps
            f=str(cout%fps/fps)
            f = f[:5].split(".")
            f = f[-1]
            if len(f) == 1:
                f = f +"00"
            if len(f) == 2:
                f = f +"0"
            second = int(cout/fps - 60*int(cout/(fps*60)))
            if second < 0:
                second = 0
            time_end = '{h:02d}:{m:02d}:{s:02d},{f}'.format(h = int(cout/(fps*60*60)),m=int(cout/(fps*60)),s=second,f = str(f))         
            list_time_start.append(time_start)
            list_time_end.append(time_end)
            list_sub.append(sub_text)
            if len(list_sub) >=2:
                if SequenceMatcher(None, sub_text.lower(), list_sub[-2].lower()).ratio() > 0.95:
                    list_time_end[-2] = time_end
                    del list_time_end[-1]
                    del list_time_start[-1]
                    del list_sub[-1]
            list_t = []
            check = 1
            soluongf = 5
            stt +=1
                    
        
                
        count +=1
       
    for s in range(len(list_time_start)):
    
        sub += str(s+1) + "\n" + list_time_start[s] + "  -->  " + list_time_end[s] + "\n" + list_sub[s] + "\n" + "\n"
    print(sub)
    return sub

    
sub = get_text_in_img("/home/amnhacsaigon/hoanchu/gen_text_in_img/video/a_a.mp4",langs[language],x,y,width,height,start)
print(sub)
    