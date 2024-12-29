import tkinter as tk
from tkinter import filedialog, messagebox
import os
import bibtexparser
import re

def select_files():
    files = filedialog.askopenfilenames(filetypes=[("Bib文件", "*.bib")])
    file_paths.set("\n".join(files))

def clean_key(key, used_keys):
    """
    清理并确保键值唯一。
    """
    if not key:
        key = 'unknown'
    # 替换非字母、数字和下划线的字符为下划线
    cleaned_key = re.sub(r'[^a-zA-Z0-9_]', '_', key)
    # 去除连续的下划线
    cleaned_key = re.sub(r'_+', '_', cleaned_key)
    original_key = cleaned_key
    suffix = 1
    # 确保键值唯一
    while cleaned_key in used_keys:
        cleaned_key = f"{original_key}_{suffix}"
        suffix += 1
    used_keys.add(cleaned_key)
    return cleaned_key

def is_duplicate(entry1, entry2):
    """
    检查两个条目是否重复（基于内容）。
    """
    if 'doi' in entry1 and 'doi' in entry2:
        return entry1['doi'] == entry2['doi']
    # 使用标题、作者、年份、期刊/出版社生成唯一标识
    identifier1 = f"{entry1.get('title', '')}_{entry1.get('author', '')}_{entry1.get('year', '')}_{entry1.get('journal', '') or entry1.get('publisher', '')}"
    identifier2 = f"{entry2.get('title', '')}_{entry2.get('author', '')}_{entry2.get('year', '')}_{entry2.get('journal', '') or entry2.get('publisher', '')}"
    return identifier1.lower().replace(' ', '') == identifier2.lower().replace(' ', '')

def process_entries(entries):
    processed = {}
    duplicates = {}
    cleaned_keys = {}
    used_keys = set()
    for entry in entries:
        original_key = entry.get('ID', '')
        entry['ID'] = clean_key(original_key, used_keys)
        # 记录清理前后的键值对照
        if entry['ID'] != original_key:
            cleaned_keys[original_key] = entry['ID']
        # 创建唯一标识
        identifier = entry.get('doi', '')
        if not identifier:
            identifier = f"{entry.get('title', '')}_{entry.get('author', '')}_{entry.get('year', '')}_{entry.get('journal', '') or entry.get('publisher', '')}"
            identifier = identifier.lower().replace(' ', '')
        # 检查是否重复
        if identifier in processed:
            if identifier not in duplicates:
                duplicates[identifier] = []
            duplicates[identifier].append(entry['ID'])
        else:
            processed[identifier] = entry
    # 提取所有条目
    new_entries = list(processed.values())
    # 提取重复的ID
    duplicate_ids = [ids for ids_list in duplicates.values() for ids in ids_list]
    return new_entries, duplicate_ids, cleaned_keys

def merge_bib():
    selected_files = file_paths.get().split('\n')
    if not selected_files:
        messagebox.showerror("错误", "请选择至少一个Bib文件。")
        return
    # 让用户选择保存位置
    save_path = filedialog.asksaveasfilename(defaultextension=".bib", filetypes=[("Bib文件", "*.bib")])
    if not save_path:
        messagebox.showinfo("提示", "未选择保存位置，操作取消。")
        return
    # 检查文件是否已存在
    if os.path.exists(save_path):
        overwrite = messagebox.askyesno("确认", f"文件 {save_path} 已存在，是否覆盖？")
        if not overwrite:
            messagebox.showinfo("提示", "操作取消。")
            return
    entries = []
    for file in selected_files:
        try:
            with open(file, 'r', encoding='utf-8') as bibtex_file:
                bib_database = bibtexparser.load(bibtex_file)
                entries.extend(bib_database.entries)
        except Exception as e:
            messagebox.showerror("错误", f"读取文件 {file} 时出错：{str(e)}")
            return
    new_entries, duplicate_ids, cleaned_keys = process_entries(entries)
    new_bib_database = bibtexparser.bibdatabase.BibDatabase()
    new_bib_database.entries = new_entries
    try:
        with open(save_path, 'w', encoding='utf-8') as bibtex_file:
            bibtexparser.dump(new_bib_database, bibtex_file)
    except Exception as e:
        messagebox.showerror("错误", f"保存文件时出错：{str(e)}")
        return
    # 清除已选文件列表
    file_paths.set("")
    messages = []
    if cleaned_keys:
        msg = "以下键值被清理并替换为合法键值：\n"
        for original, cleaned in cleaned_keys.items():
            msg += f"{original} -> {cleaned}\n"
        messages.append(msg)
    if duplicate_ids:
        msg = "以下键值重复，已被移除：\n"
        msg += "\n".join(duplicate_ids)
        messages.append(msg)
    if messages:
        messagebox.showinfo("处理结果", "\n\n".join(messages))
    else:
        messagebox.showinfo("合并完成", "Bib文件合并完成，没有重复键值且所有键值合法。")

root = tk.Tk()
root.title("Bib文件合并工具")

# 程序功能简介
intro_label = tk.Label(root, text="本工具用于合并多个Bib文件，并自动清理和去重条目。", wraplength=400, justify="center")
intro_label.pack(pady=10)

file_frame = tk.Frame(root)
file_frame.pack(pady=10)

select_button = tk.Button(file_frame, text="选择Bib文件", command=select_files)
select_button.pack(side="left")

file_paths = tk.StringVar()
file_list = tk.Label(file_frame, textvariable=file_paths, wraplength=400, justify="left")
file_list.pack(side="left")

merge_button = tk.Button(root, text="合并Bib文件", command=merge_bib)
merge_button.pack(pady=10)

root.mainloop()