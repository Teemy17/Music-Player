import os
import io
import random

try:
    from tkinter import *
    from tkinter import filedialog, messagebox
except ImportError:
    print("Tkinter not found. Please install Tkinter.")

try:
    import pygame.mixer as mixer
except ImportError:
    print("Pygame not found. Please install Pygame.")

try:
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3
except ImportError:
    print("Mutagen not found. Please install Mutagen.")

try:
    from PIL import ImageTk, Image
except ImportError:
    print("Pillow not found. Please install Pillow.")


class BaseButton:
    def __init__(self, root, app, image_path, x, y, button_size=(80, 80)):
        self.app = app
        self.button = Button(root, highlightthickness=0, bd=0)
        self.button_img = ImageTk.PhotoImage(
            Image.open(image_path).resize(button_size, Image.LANCZOS)
        )
        self.button.config(image=self.button_img, command=self.action)
        self.button.place(x=x, y=y)

    # Get the album art from the song
    def get_album_art(self, song_path):
        audio = MP3(song_path, ID3=ID3)
        album_art = None
        for tag in audio.tags.values():
            if tag.FrameID.startswith("APIC"):
                if tag.mime.startswith("image/jpeg"):
                    album_art = tag
                break
        if album_art:
            return album_art
        else:
            return None

    def load_image(self, image_path, button_size):
        self.button_img = ImageTk.PhotoImage(
            Image.open(image_path).resize(button_size, Image.LANCZOS)
        )


class PlayButton(BaseButton):
    def action(self):
        if self.app.song_list.curselection():
            song_info = self.app.directory_list[self.app.song_list.curselection()[0]]
            mixer.music.load(song_info["path"] + song_info["song"])
            mixer.music.play()

            self.app.current_song_index = self.app.song_list.curselection()[0]
            song_type = MP3(song_info["path"] + song_info["song"])
            self.app.song_length = song_type.info.length
            self.app.display_current_song()

            album_art = self.get_album_art(song_info["path"] + song_info["song"])
            self.app.display_album_art(album_art)

            SongDuration(self.app).song_duration_time()
        else:
            messagebox.showerror("Error", "Please select a song to play")


class PauseButton(BaseButton):
    def action(self):
        if self.app.paused == False and mixer.music.get_busy():
            mixer.music.pause()
            self.change_button_image("Images/unpause.png")
            self.app.paused = True
        else:
            mixer.music.unpause()
            self.app.paused = False
            self.change_button_image("Images/pause.png")
            SongDuration(self.app).song_duration_time()

    def change_button_image(self, new_image_path):
        self.load_image(new_image_path, button_size=(80, 80))
        self.button.configure(image=self.button_img, command=self.action)


class StopButton(BaseButton):
    def action(self):
        mixer.music.stop()
        self.app.song_list.select_clear(0, END)
        self.app.paused = False
        self.app.display_current_song_reset()
        self.app.display_album_art(None)
        self.app.current_song_index = 0
        SongDuration(self.app)

        if isinstance(self.app.btAutoPlay_img, AutoPlayButton):
            self.app.btAutoPlay_img.disable_autoplay()


class NextButton(BaseButton):
    def action(self):
        if self.app.current_song_index + 1 < len(self.app.directory_list):
            next_song_index = self.app.current_song_index + 1
            song_info = self.app.directory_list[next_song_index]
            mixer.music.load(song_info["path"] + song_info["song"])
            mixer.music.play()
            self.app.current_song_index = next_song_index
            self.app.song_list.select_clear(0, END)
            self.app.song_list.select_set(next_song_index)
            self.app.song_list.activate(next_song_index)
            self.app.display_current_song()

            album_art = self.get_album_art(song_info["path"] + song_info["song"])
            self.app.display_album_art(album_art)

            SongDuration(self.app).song_duration_time()

        else:
            print("No more songs in the list")


class PrevButton(BaseButton):
    def action(self):
        if self.app.current_song_index > 0:
            prev_song_index = self.app.current_song_index - 1
            song_info = self.app.directory_list[prev_song_index]
            mixer.music.load(song_info["path"] + song_info["song"])
            mixer.music.play()
            self.app.current_song_index = prev_song_index
            self.app.song_list.select_clear(0, END)
            self.app.song_list.select_set(prev_song_index)
            self.app.song_list.activate(prev_song_index)
            self.app.display_current_song()

            album_art = self.get_album_art(song_info["path"] + song_info["song"])
            self.app.display_album_art(album_art)

            SongDuration(self.app).song_duration_time()

        else:
            print("This is the first song in the list")


class DeleteButton(BaseButton):
    def __init__(self, root, app, image_path, x, y, button_size=(80, 80)):
        super().__init__(root, app, image_path, x, y, button_size)

    def action(self):
        selected_index = self.app.song_list.curselection()
        if selected_index:
            selected_song = self.app.directory_list.pop(selected_index[0])
            if selected_index[0] == self.app.current_song_index:
                StopButton.action(self)
            self.app.song_list.delete(selected_index[0])
            print(f"Deleted song: {selected_song}")
        else:
            messagebox.showerror("Error", "Please select a song to delete")


class AutoPlayButton(BaseButton):
    def __init__(self, root, app, image_path, x, y, button_size=(80, 80)):
        super().__init__(root, app, image_path, x, y, button_size)
        self.autoplay_enabled = False
        self.root = root

    def action(self):
        if self.autoplay_enabled == False:
            self.enable_autoplay()
        elif self.autoplay_enabled == True:
            self.disable_autoplay()

    def enable_autoplay(self):
        self.autoplay_enabled = True
        self.change_button_image("Images/autoon.png")
        print("Autoplay enabled")
        self.play_next_song_after_delay()

    def play_next_song_after_delay(self):
        if self.autoplay_enabled:
            self.check_music_status()
            self.root.after(1000, self.play_next_song_after_delay)

    def disable_autoplay(self):
        self.autoplay_enabled = False
        self.change_button_image("Images/autooff.png")
        print("Autoplay disabled")

    def check_music_status(self):
        if not mixer.music.get_busy() and self.app.paused == False:
            self.play_next_song()

    def play_next_song(self):
        if self.autoplay_enabled:
            if self.app.current_song_index + 1 < len(self.app.directory_list):
                next_song_index = self.app.current_song_index + 1
                song_info = self.app.directory_list[next_song_index]
                mixer.music.load(song_info["path"] + song_info["song"])
                mixer.music.play()
                self.app.current_song_index = next_song_index
                self.app.song_list.select_clear(0, END)
                self.app.song_list.select_set(next_song_index)
                self.app.song_list.activate(next_song_index)
                self.app.display_current_song()

                album_art = self.get_album_art(song_info["path"] + song_info["song"])
                self.app.display_album_art(album_art)

                SongDuration(self.app).song_duration_time()
            else:
                print("No more songs in the list")
                self.disable_autoplay()

    def change_button_image(self, new_image_path):
        self.load_image(new_image_path, button_size=(50, 50))
        self.button.configure(image=self.button_img, command=self.action)


class ShuffleButton(BaseButton):
    def __init__(self, root, app, image_path, x, y, button_size=(80, 80)):
        super().__init__(root, app, image_path, x, y, button_size)

    # Shuffle the song in the list
    def action(self):
        if not self.app.directory_list == []:
            random.shuffle(self.app.directory_list)
            self.app.song_list.delete(0, END)
            for song_info in self.app.directory_list:
                self.app.song_list.insert(END, song_info["song"])

            self.app.current_song_index = 0
            self.app.song_list.select_set(0)
        else:
            messagebox.showerror("Error no song", "No songs in the list to shuffle")


class App:
    def __init__(self, root):
        self.window = root
        mixer.init()
        self.main_window()
        self.directory_list = []
        self.option_menu()

        self.current_song_index = 0
        self.paused = False

        self.song_duration_bar = 0
        self.song_length = 0

        self.display_album_art(None)

    def main_window(self):
        Label(
            self.window, text="Music Player", font=("Arial", 20, "bold", "italic")
        ).place(x=320, y=20)

        frame = Frame(self.window)
        frame.place(x=30, y=70)
        v_scroll = Scrollbar(frame)
        v_scroll.pack(side=RIGHT, fill=Y)

        self.song_list = Listbox(
            frame,
            bg="#404040",
            fg="#ffbf50",
            width=120,
            height=12,
            font=("Arial", 8, "bold"),
            relief=SUNKEN,
            borderwidth=2,
            yscrollcommand=v_scroll.set,
        )
        self.song_list.pack(side=LEFT)
        v_scroll.configure(command=self.song_list.yview)

        self.volume_label = Label(
            self.window, text="Volume", font=("Arial", 12, "bold"), fg="black"
        )
        self.volume_label.place(x=650, y=380)
        self.volume_slider = Scale(
            self.window, from_=0, to=100, orient=HORIZONTAL, command=self.volume
        )
        self.volume_slider.set(50)
        self.volume_slider.place(x=650, y=400)

        self.btPlay_img = PlayButton(self.window, self, "Images/play.png", 250, 250)
        self.btPause_img = PauseButton(self.window, self, "Images/pause.png", 350, 250)
        self.btStop_img = StopButton(self.window, self, "Images/stop.png", 450, 250)
        self.btNext_img = NextButton(self.window, self, "Images/next.png", 550, 250)
        self.btPrev_img = PrevButton(self.window, self, "Images/prev.png", 150, 250)
        self.btDelete_img = DeleteButton(
            self.window, self, "Images/delete.png", 50, 260, (40, 40)
        )
        self.btAutoPlay_img = AutoPlayButton(
            self.window, self, "Images/autooff.png", 710, 270, (50, 50)
        )
        self.btShuffle_img = ShuffleButton(
            self.window, self, "Images/shuffle.png", 720, 350, (40, 40)
        )

        self.autoplay_label = Label(
            self.window, text="Autoplay", font=("Arial", 12, "bold"), fg="black"
        ).place(x=700, y=250)
        self.autoplay_label_on = Label(
            self.window, text="On", font=("Arial", 12), fg="black"
        ).place(x=740, y=320)
        self.autoplay_label_off = Label(
            self.window, text="Off", font=("Arial", 12), fg="black"
        ).place(x=700, y=320)
        self.current_song_label = Label(
            self.window, text="Song label", font=("Arial", 12), fg="white", bg="#141414"
        )
        self.delete_song_label = Label(
            self.window, text="Delete", font=("Arial", 12), fg="black"
        ).place(x=50, y=300)

        self.current_song_label.place(x=250, y=450)
        self.album_art_label = Label(self.window, bg="#141414", relief=SUNKEN)
        self.album_art_label.place(x=30, y=330, width=150, height=150)

    def option_menu(self):
        menubar = Menu(self.window)
        self.window.config(menu=menubar)

        options_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=options_menu)
        options_menu.add_command(label="Add songs", command=self.add_song)
        options_menu.add_command(label="Add folder", command=self.add_folder)

    def add_song(self):
        try:
            songs = filedialog.askopenfilenames(
                title="Select one or multiple song", filetypes=[("mp3 Files", "*.mp3")]
            )
            for song in songs:
                song_name = os.path.basename(song)
                directory_path = song.replace(song_name, "")
                # Check if the song is already in the list
                if not any(item["song"] == song_name for item in self.directory_list):
                    self.directory_list.append(
                        {"path": directory_path, "song": song_name}
                    )
                    self.song_list.insert(END, song_name)
                else:
                    messagebox.showerror("Error", f"{song_name} is already in the list")

            self.song_list.select_set("0")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def add_folder(self):
        try:
            folder_path = filedialog.askdirectory(
                title="Select a folder containing songs"
            )
            if folder_path:
                songs = [
                    file for file in os.listdir(folder_path) if file.endswith(".mp3")
                ]
                if songs:
                    for song in songs:
                        song_name = os.path.basename(song)
                        # Check if the song is already in the list
                        if not any(
                            item["song"] == song_name for item in self.directory_list
                        ):
                            self.directory_list.append(
                                {"path": folder_path + "/", "song": song_name}
                            )
                            self.song_list.insert(END, song_name)

                    self.song_list.select_set(0)
                else:
                    messagebox.showinfo(
                        "Info", "No MP3 files found in the selected folder."
                    )
            else:
                messagebox.showinfo("Info", "No folder selected.")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    # Attain album art from the song if available
    def display_album_art(self, album_art):
        if album_art is not None:
            img_data = album_art.data
            img = Image.open(io.BytesIO(img_data))
            img = img.resize((150, 150), Image.LANCZOS)
            album_art_img = ImageTk.PhotoImage(img)
            self.album_art_label.config(image=album_art_img)
            self.album_art_label.image = album_art_img
        else:
            default_img_path = "Images/default.png"
            default_img = Image.open(default_img_path)
            default_img = default_img.resize((150, 150), Image.LANCZOS)

            default_album_art_img = ImageTk.PhotoImage(default_img)
            self.album_art_label.config(image=default_album_art_img)
            self.album_art_label.image = default_album_art_img

    def volume(self, val):
        volume = int(val) / 100
        mixer.music.set_volume(volume)

    def display_current_song(self):
        if self.directory_list:
            current_song_info = self.directory_list[self.current_song_index]
            current_song_name = current_song_info["song"]
            self.current_song_label.config(
                text=f"Currently Playing: {current_song_name}"
            )

    def display_current_song_reset(self):
        self.current_song_label.config(text="Song label")


# Display the song duration in time
class SongDuration:
    def __init__(self, app):
        self.app = app
        self.song_duration_bar = Label(
            self.app.window,
            text="Song Duration",
            font=("Arial", 17, "bold"),
            fg="white",
            bg="#141414",
            width=25,
        )
        self.song_duration_bar.place(x=250, y=400)

    def update_song_duration_label(self, current_time):
        song_info = self.app.directory_list[self.app.current_song_index]
        song_type = MP3(song_info["path"] + song_info["song"])
        song_length = song_type.info.length
        self.song_duration_bar.config(
            text=f"Time is: {self.format_time(current_time)} of {self.format_time(song_length)}"
        )
        self.app.window.after(100, self.song_duration_time)

    def song_duration_time(self):
        try:
            if mixer.music.get_busy() or self.app.paused:
                current_time = mixer.music.get_pos() / 1000
                self.update_song_duration_label(current_time)
        except Exception as e:
            print("Error in song duration:", str(e))

    def format_time(self, time_in_seconds):
        minutes, seconds = divmod(int(time_in_seconds), 60)
        hours, minutes = divmod(minutes, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


if __name__ == "__main__":
    window = Tk()
    window.title("Music Player")
    window.geometry("800x500")
    window.resizable(0, 0)

    ico = Image.open("Images/icon.png")
    photo = ImageTk.PhotoImage(ico)
    window.wm_iconphoto(False, photo)

    app = App(window)
    song_duration = SongDuration(app)

    window.mainloop()
