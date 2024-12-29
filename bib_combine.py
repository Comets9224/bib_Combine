import tkinter as tk
from tkinter import filedialog, messagebox
import os
import bibtexparser
import re
import hashlib


def select_files():
    files = filedialog.askopenfilenames(filetypes=[("BibTeX files", "*.bib;*.bibtex")])
    file_paths.set("\n".join(files))


def clean_title_as_key(title, used_keys):
    if not title:
        title = 'unknown'
    # 替换非法字符为下划线
    cleaned_key = re.sub(r'[^a-zA-Z0-9_]', '_', title)
    cleaned_key = re.sub(r'_+', '_', cleaned_key)
    cleaned_key = cleaned_key[:30]  # 限制长度
    if cleaned_key and cleaned_key[0].isdigit():
        cleaned_key = '_' + cleaned_key  # 如果以数字开头，添加下划线
    original_key = cleaned_key
    suffix = 1
    while cleaned_key in used_keys:
        cleaned_key = f"{original_key}_{suffix}"  # 确保键值唯一
        suffix += 1
    used_keys.add(cleaned_key)
    return cleaned_key


def generate_unique_identifier(entry):
    # 生成条目的唯一标识符
    fields = ''.join(f"{key}{str(value if value is not None else '').lower().replace(' ', '')}"
                     for key, value in sorted(entry.items()))
    return hashlib.sha256(fields.encode()).hexdigest()


def process_entries(entries):
    processed = {}
    duplicates = {}
    for entry in entries:
        identifier = generate_unique_identifier(entry)
        if identifier in processed:
            duplicates.setdefault(identifier, []).append(entry['ID'])
        else:
            processed[identifier] = entry
    new_entries = list(processed.values())
    duplicate_ids = [ids for ids_list in duplicates.values() for ids in ids_list]
    return new_entries, duplicate_ids


def merge_bib():
    selected_files = file_paths.get().split('\n')
    if not selected_files:
        messagebox.showerror("错误", "请选择至少一个BibTeX文件。")
        return
    save_path = filedialog.asksaveasfilename(defaultextension=".bib", filetypes=[("BibTeX files", "*.bib;*.bibtex")])
    if not save_path:
        messagebox.showinfo("提示", "未选择保存位置，操作取消。")
        return
    if os.path.exists(save_path):
        overwrite = messagebox.askyesno("确认", f"文件 {save_path} 已存在，是否覆盖？")
        if not overwrite:
            messagebox.showinfo("提示", "操作取消。")
            return

    global_used_keys = set()
    all_entries = []

    for file in selected_files:
        print(f"Processing file: {file}")
        try:
            with open(file, 'r', encoding='utf-8') as bibtex_file:
                parser = bibtexparser.bparser.BibTexParser(common_strings=True, ignore_nonstandard_types=False)
                bib_database = bibtexparser.load(bibtex_file, parser=parser)
                print(f"Read {len(bib_database.entries)} entries from {file}")

                # 修改键值为 title 的内容，并确保全局唯一
                for entry in bib_database.entries:
                    title = entry.get('title', 'unknown')
                    cleaned_key = clean_title_as_key(title, global_used_keys)
                    entry['ID'] = cleaned_key

                all_entries.extend(bib_database.entries)

        except UnicodeDecodeError:
            try:
                with open(file, 'r', encoding='gbk') as bibtex_file:
                    parser = bibtexparser.bparser.BibTexParser(common_strings=True, ignore_nonstandard_types=False)
                    bib_database = bibtexparser.load(bibtex_file, parser=parser)
                    print(f"Read {len(bib_database.entries)} entries from {file}")

                    # 修改键值为 title 的内容，并确保全局唯一
                    for entry in bib_database.entries:
                        title = entry.get('title', 'unknown')
                        cleaned_key = clean_title_as_key(title, global_used_keys)
                        entry['ID'] = cleaned_key

                    all_entries.extend(bib_database.entries)

            except Exception as e:
                messagebox.showerror("错误", f"读取文件 {file} 时出错：{str(e)}")
                return
        except Exception as e:
            messagebox.showerror("错误", f"读取文件 {file} 时出错：{str(e)}")
            return
    print(f"Total entries read: {len(all_entries)}")

    # 处理条目，去重
    new_entries, duplicate_ids = process_entries(all_entries)
    print(f"Processed entries: {len(new_entries)}")
    print(f"Duplicates removed: {len(duplicate_ids)}")

    # 保存合并后的文件
    new_bib_database = bibtexparser.bibdatabase.BibDatabase()
    new_bib_database.entries = new_entries
    try:
        with open(save_path, 'w', encoding='utf-8') as bibtex_file:
            bibtexparser.dump(new_bib_database, bibtex_file)
    except Exception as e:
        messagebox.showerror("错误", f"保存文件时出错：{str(e)}")
        return

    # 显示处理结果
    file_paths.set("")
    messages = []
    if duplicate_ids:
        msg = "以下键值重复，已被移除：\n"
        msg += "\n".join(duplicate_ids)
        messages.append(msg)
    if messages:
        messagebox.showinfo("处理结果", "\n\n".join(messages))
    else:
        messagebox.showinfo("合并完成", "BibTeX文件合并完成，没有重复条目。")


# 创建 GUI
root = tk.Tk()
root.title("BibTeX文件合并工具")

intro_label = tk.Label(root, text="本工具用于合并多个BibTeX文件，并自动清理和去重条目。", wraplength=400,
                       justify="center")
intro_label.pack(pady=10)

file_frame = tk.Frame(root)
file_frame.pack(pady=10)

select_button = tk.Button(file_frame, text="选择BibTeX文件", command=select_files)
select_button.pack(side="left")

file_paths = tk.StringVar()
file_list = tk.Label(file_frame, textvariable=file_paths, wraplength=400, justify="left")
file_list.pack(side="left")

merge_button = tk.Button(root, text="合并BibTeX文件", command=merge_bib)
merge_button.pack(pady=10)

root.mainloop()