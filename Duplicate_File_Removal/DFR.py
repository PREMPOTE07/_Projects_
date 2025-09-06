#--------------------------------------------------------- Import Required Modules ---------------------------------------------------------------- #

import os
import hashlib
import time
from tkinter import *
from tkinter.messagebox import showerror,showinfo,showwarning ,askokcancel
from tkinter.scrolledtext import ScrolledText
from tkinter import filedialog
from tkinter import ttk
import threading
from tkinter import Toplevel, Label, Button
from tkinterdnd2 import TkinterDnD, DND_FILES
import time
from concurrent.futures import ThreadPoolExecutor

#---------------------------------------------------------- Start Window UI---------------------------------------------------------------------

# win = Tk()
win = TkinterDnD.Tk()

#------------------------------------------------ Define Global Variables----------------------------------------------------- #

DelCount = 0 # local variable for counting all deleted files
Dark_Mode = False # default light mode
scan_progress_bar = None
scan_progress_label = None
progress_bar = None
progress_label = None
FolderName = StringVar()
FolderName.set("Drag and Drop Directly")
check_var = BooleanVar()
exe_var = StringVar()

# ----------------------------------------------------  Window Setup -------------------------------------------------------- #

width = 700
height = 600

sys_width = win.winfo_screenwidth()
sys_height = win.winfo_screenheight()

center_x = int((sys_width / 2) - (width / 2))
center_y = int((sys_height / 2) - (height /2))


win.geometry(f"{width}x{height}+{center_x}+{center_y}")
win.config(bg="#F4F6F7")

win.minsize(700,600)
win.maxsize(700,600)

# win.iconbitmap("favicon.ico")

def update_title_with_time():
    current_time = time.strftime("%H:%M:%S")  
    win.title(f"Duplicates File Removal      {current_time}")
    win.after(1000, update_title_with_time)

update_title_with_time()

#------------------------------------------------- Helper Functions ----------------------------------------------------- #

#---------------------------------------------- 1.Calculate CheckSum Logic------------------------------------------- #

def CalCheckSum(path , BlockSize = 4096 * 1024): # 1 mb
    fobj = open(path , "rb")
    
    hobj = hashlib.md5()
    
    buffer = fobj.read(BlockSize)
    
    while (len(buffer) > 0):
        hobj.update(buffer)
        buffer = fobj.read(BlockSize)
        
    fobj.close()
    return hobj.hexdigest()


#-----------------------------------------------------2. Reset All Widget ----------------------------------------------------- #


def clear_deletion():
      # Clear Entry box
        FolderNameEntry.config(FolderName.set("Drag and Drop Directly"))
        check_exe.deselect()
        exe_entry.config(exe_var.set(""))
        # Hide progress bar and label safely
        try:
            if progress_bar:
                    progress_bar.place_forget()
            if progress_label:
                    progress_label.destroy()
                    progress_label.config(text="")
        except:
                pass

#---------------------------------------------------- 3. Check Folder Is Protected ------------------------------------------------- #

def is_protected_folder(path):
    protected = [
        "C:/", 
        "C:\\", 
        "C:/Windows", 
        "C:\\Windows", 
        "C:/Program Files", 
        "C:\\Program Files",
        "C:/Program Files (x86)", 
        "C:\\Program Files (x86)"
    ]
    
    
    norm_path = os.path.normpath(path).lower()
    return any(os.path.normpath(p).lower() == norm_path for p in protected)

#------------------------------------------------------------- 4.Show Success Message -------------------------------------------------------- #

def show_success_message(message="Successfully Clean"):
    popup = Toplevel(win)
    popup.title("Deleted Successfully")
    
    popup_width = 200
    popup_height = 70

   
    main_x = win.winfo_x()
    main_y = win.winfo_y()
    main_width = win.winfo_width()
    main_height = win.winfo_height()

    pos_x = main_x + (main_width // 2) - (popup_width // 2)
    pos_y = main_y + (main_height // 2) - (popup_height // 2)

    popup.geometry(f"{popup_width}x{popup_height}+{pos_x}+{pos_y}")
    popup.config(bg="#D4EDDA")  

    Label(popup, text=message, bg="#D4EDDA", fg="#155724", font=("Segoe UI", 12, "bold")).pack(pady=10)


#---------------------------------------------------- 5.Clear Placeholder when clicked ------------------------------------------------------#

def clear_placeholder(event):
    if FolderName.get() == "Drag and Drop Directly":
        FolderName.set("")

#---------------------------------------------------- 6.Clear Placeholder when clicked ------------------------------------------------------#

def restore_placeholder(event):
    if FolderName.get() == "":
        FolderName.set("Drag and Drop Directly")


#------------------------------------------------------ Core Logic ------------------------------------------------------- #

#--------------------------------------------------- 1. Find Duplicates Logic  ------------------------------------------------ #


def FindDuplicates(DirName):
    global scan_progress_bar, scan_progress_label

    TotalFils = sum(len(files) for _, _, files in os.walk(DirName))
    scanned_files = 0

    # Setup UI
    scan_var = DoubleVar(value=0)
    scan_progress_bar = ttk.Progressbar(
        win, orient="horizontal", mode="determinate",
        variable=scan_var, maximum=100
    )
    scan_progress_bar.place(x=220, y=220, width=230, height=25)

    scan_progress_label = Label(win, font=("Times New Roman", 12, "bold"), fg="black")
    scan_progress_label.place(x=475, y=210)

    scan_extra_label = Label(win, font=("Times New Roman", 10), fg="blue")
    scan_extra_label.place(x=10, y=215)

    # Notify scanning start
    schrollTextBox.insert(END, f"Scan started at: {time.ctime()}\n")
    schrollTextBox.insert(END, f"Scanning files...\n")
    schrollTextBox.see(END)
    win.update_idletasks()

    # Collect all files
    file_list = []
    for FolderNames, _, FileNames in os.walk(DirName):
        for File in FileNames:
            file_path = os.path.join(FolderNames, File)
            file_list.append(file_path)

    Duplicates = {}

    def compute_checksum(file_path):
        try:
            checksum = CalCheckSum(file_path)
            return file_path, checksum
        except:
            return file_path, None

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=os.cpu_count() * 2) as executor:
        for i, result in enumerate(executor.map(compute_checksum, file_list)):
            file_path, checksum = result
            if checksum:
                if checksum in Duplicates:
                    Duplicates[checksum].append(file_path)
                else:
                    Duplicates[checksum] = [file_path]

            scanned_files += 1

            # --- Update progress bar ---
            progress = (scanned_files / TotalFils) * 100
            scan_var.set(progress)

            elapsed_time = time.time() - start_time
            remaining_files = TotalFils - scanned_files
            if scanned_files > 0:
                time_per_file = elapsed_time / scanned_files
                remaining_time = int(time_per_file * remaining_files)
            else:
                remaining_time = 0

            scan_progress_label.config(text=f"Scanning: {int(progress)} %")
            scan_extra_label.config(
                text=f"Remaining: {remaining_files} files | {remaining_time} sec left"
            )

            win.update_idletasks()
            if scanned_files % 10 == 0 or scanned_files == TotalFils:
                schrollTextBox.see(END)

    schrollTextBox.insert(END, f"Total Scanned Files: {TotalFils}\n")
    schrollTextBox.see(END)

    # Clean up UI
    scan_progress_bar.destroy()
    scan_progress_label.destroy()
    scan_extra_label.destroy()

    return Duplicates




#-------------------------------------------------- 2.Delete All Duplicates --------------------------------------------------- #


def DeleteDuplicates(DirName):
    timeStamp = time.ctime()

    log_path = os.path.join(DirName, "DuplicatesDeletion.log")
    with open(log_path, "a") as fobj:  # Always open in append mode
        global progress_bar, progress_label

        really = askokcancel(title="", message="Are you sure you want to delete all duplicate files?")

        if really:
            MyDict = FindDuplicates(DirName)
            result = list(filter(lambda x: len(x) > 1, MyDict.values()))

            DupliFilesList = []
            global DelCount
            DelCount = 0

            files_to_delete = []
            for value in result:
                files_to_delete.extend(value[1:])  # keep only duplicates

            total_files = len(files_to_delete)

            if total_files == 0:
                schrollTextBox.insert(END, "No duplicates found.\n")
                schrollTextBox.see(END)
                clear_deletion()
                return

            progress_var = DoubleVar()
            progress_bar = ttk.Progressbar(win, orient="horizontal", mode="determinate", variable=progress_var, maximum=100)
            progress_bar.place(x=220, y=210, width=230, height=25)

            progress_label = Label(win, text="", font=("Times New Roman", 14, "bold"), fg="green", bg=None)
            progress_label.place(x=520, y=210)

            for i, file_path in enumerate(files_to_delete):
                try:
                    if os.path.exists(file_path):
                        fobj.write(f"{file_path}: {timeStamp} \n")
                        os.remove(file_path)
                        rel_path = os.path.relpath(file_path, DirName)
                        DupliFilesList.append(rel_path)
                        DelCount += 1

                        schrollTextBox.insert(END, f"Deleted: {rel_path}\n")
                    else:
                        schrollTextBox.insert(END, f"File already deleted or not found: {file_path}\n")

                    progress = ((i + 1) / total_files) * 100
                    progress_var.set(progress)
                    progress_label.config(text=f"{int(progress)} %")
                    progress_bar.update()
                    schrollTextBox.see(END)

                except PermissionError:
                    schrollTextBox.insert(END, f"Permission denied: {file_path}\n")
                except Exception as e:
                    schrollTextBox.insert(END, f"Error deleting {file_path}: {e}\n")

            schrollTextBox.insert(END, f"\nTotal Deleted Files: {DelCount}\n")
            progress_label.destroy()
            progress_bar.destroy()
            clear_deletion()
            showinfo(title="Sucess Message",message="Sucessfully Deleted All Duplicates")
            showinfo(title="Note", message="A log file is created at same folder")
        else:
            clear_deletion()

#-------------------------------------------- 3. Delete All Duplicates with extension olny --------------------------------------------- #

def DeleteDuplicates_with_exe(DirName,exe):
    timeStamp = time.ctime()

    log_path = os.path.join(DirName, "DuplicatesDeletion.log")
    with open(log_path, "a") as fobj:  # Always open in append mode
        global progress_bar, progress_label

        really = askokcancel(title="", message="Are you sure you want to delete all duplicate files?")

        if really:
            MyDict = FindDuplicates(DirName)
            result = list(filter(lambda x: len(x) > 1, MyDict.values()))

            DupliFilesList = []
            global DelCount
            DelCount = 0

            files_to_delete = []
            for value in result:
                files_to_delete.extend(value[1:])  # keep only duplicates

            total_files = len(files_to_delete)

            if total_files == 0:
                schrollTextBox.insert(END, "No duplicates found.\n")
                schrollTextBox.see(END)
                clear_deletion()
                return

            progress_var = DoubleVar()
            progress_bar = ttk.Progressbar(win, orient="horizontal", mode="determinate", variable=progress_var, maximum=100)
            progress_bar.place(x=220, y=210, width=230, height=25)

            progress_label = Label(win, text="", font=("Times New Roman", 14, "bold"), fg="green", bg=None)
            progress_label.place(x=520, y=210)

            for i, file_path in enumerate(files_to_delete):
                try:
                    if os.path.exists(file_path):
                        fobj.write(f"{file_path}: {timeStamp} \n")
                        if file_path.endswith(exe):
                            os.remove(file_path)
                            rel_path = os.path.relpath(file_path, DirName)
                            DupliFilesList.append(rel_path)
                            DelCount += 1
                            schrollTextBox.insert(END, f"Deleted: {rel_path}\n")


                        schrollTextBox.insert(END, f"Deleted: {rel_path}\n")
                    else:
                        schrollTextBox.insert(END, f"File already deleted or not found: {file_path}\n")

                    progress = ((i + 1) / total_files) * 100
                    progress_var.set(progress)
                    progress_label.config(text=f"{int(progress)} %")
                    progress_bar.update()
                    schrollTextBox.see(END)

                except PermissionError:
                    schrollTextBox.insert(END, f"Permission denied: {file_path}\n")
                except Exception as e:
                    schrollTextBox.insert(END, f"Error deleting {file_path}: {e}\n")

            schrollTextBox.insert(END, f"\nTotal Deleted Files: {DelCount}\n")
            progress_label.destroy()
            progress_bar.destroy()
            clear_deletion()
            showinfo(title="Sucess Message",message="Sucessfully Deleted All Duplicates")
            showinfo(title="Note", message="A log file is created at same folder")
        else:
            clear_deletion()
            
#------------------------------------------------- 4. Final Delete Files Logic -------------------------------------------------------- #

def check_exe_test():   # check checkbox is clicked or not
    return check_var.get()

def Delete_files():
    folder = FolderName.get()
    
    if is_protected_folder(folder):
        showwarning("Protected Folder", " You cannot run this tool on C: drive or system folders!")
        clear_deletion()
        return
    if check_exe_test():   
        if exe_var.get().strip() == "":
            showwarning(title="Extension Field Empty", message="Please Give Extension For Delete Files")
            return
        else:
            DeleteDuplicates_with_exe(FolderName.get(), exe_var.get().strip())
            clear_deletion()
    else:
        DeleteDuplicates(FolderName.get())
        
   
#------------------------------------------------------------- Theme Logic --------------------------------------------------------------- #
            

#-------------------------------------------------------- 1.Apply Dark or Light mode ------------------------------------------------- #

def apply_theme():
    global Dark_Mode
    bg_color = "#1E1E1E" if Dark_Mode else "#F4F6F7"
    fg_color = "#FFFFFF" if Dark_Mode else "#000000"
    entry_bg = "#2E2E2E" if Dark_Mode else "#FFFFFF"
    text_bg = "#2E2E2E" if Dark_Mode else "#FFFFFF"
    text_fg = "#FFFFFF" if Dark_Mode else "#000000"
    
    win.config(bg=bg_color)
    FolderNameLabel.config(bg = bg_color,fg=fg_color)
    FolderNameEntry.config(bg=entry_bg,fg=fg_color,insertbackground=fg_color)
    BrowseBtn.config(bg=bg_color,fg=fg_color)
    DeleteDuplicateBtn.config(bg="red",fg="white")
    ToggleThemeBtn.config(bg=bg_color,fg=fg_color)
    schrollTextBox.config(bg=text_bg,fg=text_fg,insertbackground=text_fg)
    
    check_exe.config(bg=bg_color, fg=fg_color, selectcolor=bg_color, activebackground=bg_color, activeforeground=fg_color)
    exe_entry.config(bg=entry_bg, fg=fg_color, insertbackground=fg_color)

#---------------------------------------------------------------- 2.Toggle Function Logic -------------------------------------------------------- #


def Toggle_Mode():
    global Dark_Mode
    Dark_Mode = not Dark_Mode
    ToggleThemeBtn.config(text="🌞 Light Mode" if Dark_Mode else "🌙 Dark Mode")
    apply_theme()
    

#----------------------------------------------------------- Folder Input (Browser and Drop Logic) ----------------------------------------------- #

#------------------------------------------------------------------- 1.Drop Folder --------------------------------------------------------------- #
     
def drop_folder(event):
    folder_path = event.data.strip("{}") 
    if os.path.isdir(folder_path):
        FolderName.set(folder_path)
        schrollTextBox.insert(END, f"Dropped folder: {folder_path}\n")
        schrollTextBox.see(END)
    else:
        showwarning("Invalid", "Please drop a valid folder.")        

   
#-------------------------------------------------------------- 2.Get Folder Name ---------------------------------------------------------------- #
   

def DirectoryName():
    var = filedialog.askdirectory(initialdir="/" ,title="Select Directory")
    FolderName.set(var)
    
#-------------------------------------------------------  UI Widget ------------------------------------------------------------------ #

WarningLabel = Label(win, 
    text="⚠️ Please Don't try on C: Drive folders or Application folders!",
    font=("Times New Roman", 12, "bold"), 
    fg="red", bg="lightyellow",relief="sunken"
)
WarningLabel.place(x=155, y=4)

FolderNameLabel = Label(win, text="FolderName : ",font=("Modern",20 , "bold"),fg="black")
FolderNameLabel.place(x=20,y=40)


FolderNameEntry = Entry(win,relief="sunken",font=("Modern",14),textvariable=FolderName,bd=2)
FolderNameEntry.place(x=200,y=40,height=40,width=380)

FolderNameEntry.drop_target_register(DND_FILES) #Register drag & drop
FolderNameEntry.dnd_bind('<<Drop>>', drop_folder)

FolderNameEntry.bind("<FocusIn>", clear_placeholder)
FolderNameEntry.bind("<FocusOut>", restore_placeholder)

BrowseBtn = Button(win ,text="Browse" , font=("Times New Roman",20) , relief="sunken" , cursor="plus",command=DirectoryName)
BrowseBtn.place(x=280,y=90 , height=44 , width=120)

DeleteDuplicateBtn = Button(win, text="Delete Duplicates",bg="red",fg="white",font=("Arial",14),command=lambda: threading.Thread(target=Delete_files, daemon=True).start())
DeleteDuplicateBtn.place(x=260,y=180,height=35,width=165)

schrollTextBox = ScrolledText(win)
schrollTextBox.place(x=20,y=250,height=310,width=670)

clear_textBX_btn = Button(win,text="Clear",relief="sunken",font=("Times New Roman",14),command=lambda: schrollTextBox.delete("1.0", END))
clear_textBX_btn.place(x=600,y=260,height=30 , width=60) 

ToggleThemeBtn = Button(win,text="🌙 Dark Mode",relief="sunken",font=("Times New Roman",12),command=Toggle_Mode)
ToggleThemeBtn.place(x=587,y=42)

check_exe = Checkbutton(win,text="Delete with extension only",font=("Times New Roman",16),fg="black",variable=check_var,command=check_exe_test)
check_exe.place(x=200,y=140)

exe_entry = Entry(win,font=(30),bd=3,relief="sunken",textvariable=exe_var)
exe_entry.place(x=460,y=148,width=80,height=27)

win.mainloop()

#------------------------------------------------------------------- END ------------------------------------------------------------------------------------------ #
    