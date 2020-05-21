import sys
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog

class ModeSelector(tk.Frame):

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.__make_widgets()


    def __make_widgets(self):
        RBW = 7
        frm_role = tk.Frame(self, relief=tk.SUNKEN, bd=2)
        frm_role.pack(fill=tk.X, expand=True, ipadx=5, pady=5)
        self.role = tk.StringVar()
        captain = ttk.Radiobutton(
            frm_role, text="Captain", variable=self.role,
            value='captain', width=RBW)
        captain.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        fo = ttk.Radiobutton(
            frm_role, text="FO", variable=self.role,
            value='fo', width=RBW)
        fo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        frm_rb = tk.Frame(self, relief=tk.SUNKEN, bd=2)
        frm_rb.pack(fill=tk.X, expand=True, ipadx=5, pady=5)
        self.var = tk.StringVar()
        online = ttk.Radiobutton(
            frm_rb, text="Online", command=self.__onPress,
            variable=self.var, value='online', width=RBW)
        online.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        offline = ttk.Radiobutton(
            frm_rb, text="Offline", command=self.__onPress,
            variable=self.var, value='offline', width=RBW)
        offline.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        self.frm_online = tk.Frame(self)
        self.frm_online.pack(fill=tk.X, expand=True, pady=5)
        ttk.Label(self.frm_online, text="Username:").pack(anchor="w")
        self.username = ttk.Entry(self.frm_online, width=0)
        self.username.pack(fill=tk.X, expand=True)
        ttk.Label(self.frm_online, text="Password:").pack(anchor="w")
        self.password = ttk.Entry(self.frm_online, show='*', width=0)
        self.password.pack(fill=tk.X, expand=True)
        ttk.Label(self.frm_online, text="Months:").pack(anchor="w")
        self.months = ttk.Spinbox(self.frm_online, width=0, from_=1, to=60)
        self.months.insert(0, 1)
        self.months.pack(fill=tk.X, expand=True)
        online.invoke()
        captain.invoke()


    def __onPress(self):
        if self.var.get() == "offline":
            self.frm_online.pack_forget()
            self.mode = 'offline'
        else:
            self.frm_online.pack(fill=tk.X, expand=True)
            self.mode = 'online'


class Actions(tk.Frame):

    def __init__(self, parent, ms, txt):
        tk.Frame.__init__(self, parent)
        self.make_widgets()
        self.ms = ms
        self.txt = txt


    def make_widgets(self):
        frm_1 = tk.Frame(self)
        frm_1.pack(fill=tk.X)
        btn_csv = ttk.Button(
            frm_1, text="Logbook (csv)",
            width=0, command=self.csv)
        btn_csv.pack(fill=tk.X)
        btn_ical = ttk.Button(
            frm_1, text="Roster (ical)",
            width=0, command=self.ical)
        btn_ical.pack(fill=tk.X)

        frm_2 = tk.Frame(self)
        frm_2.pack(fill=tk.X, pady=10)
        btn_save = ttk.Button(
            frm_2, text="Save",
            width=0, command=self.save)
        btn_save.pack(fill=tk.X)
        btn_copy = ttk.Button(
            frm_2, text="Copy",
            width=0, command=self.copy)
        btn_copy.pack(fill=tk.X)

        frm_3 = tk.Frame(self)
        frm_3.pack(fill=tk.X)
        btn_quit = ttk.Button(frm_3, text="Quit", width=0, command=sys.exit)
        btn_quit.pack(fill=tk.X)


    def csv(self):
        with open("test.csv") as f:
            self.txt.delete('0.1', tk.END)
            self.txt.insert('0.1', f.read())


    def ical(self):
        with open("test.ical") as f:
            self.txt.delete('0.1', tk.END)
            self.txt.insert('0.1', f.read())


    def copy(self):
        tl = self.winfo_toplevel()
        tl.clipboard_clear()
        tl.clipboard_append(self.txt.get('0.1', tk.END))
        messagebox.showinfo('Copy', 'Text copied to clipboard.')


    def save(self):
        fn = filedialog.asksaveasfilename()
        print(fn)


class MainWindow(tk.Frame):

    def __init__(self, parent=None):
        tk.Frame.__init__(self, parent)
        self.make_widgets()


    def make_widgets(self):
        sidebar = tk.Frame(self, bd=2, width=0)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        txt = tk.Text(self)
        txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb = ttk.Scrollbar(self)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        sb.config(command=txt.yview)
        txt.config(yscrollcommand=sb.set)
        ms = ModeSelector(sidebar).pack()
        ttk.Separator(sidebar, orient="horizontal").pack(fill=tk.X, pady=20)
        Actions(sidebar, ms, txt).pack(fill=tk.BOTH, expand=True, side=tk.BOTTOM)


def main() -> int:
    root = tk.Tk()
    root.title("aimstool")
    MainWindow(root).pack(fill=tk.BOTH, expand=True)
    root.mainloop()


if __name__ == "__main__":
    main()
