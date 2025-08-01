# backend/file_tools.py

import os
import re
import shutil
from typing import List, Tuple


DEFAULT_PATTERN_CONFIG = [
    {
        "name": "提取 EP 后面的数字",
        "pattern": r"EP(\d+)",
        "rename_func": lambda m: m.group(1),
    },
    {
        "name": "提取第一个数字串",
        "pattern": r"(\d+)",
        "rename_func": lambda m: m.group(1),
    },
]


def preview_subfolders(root_folder: str) -> List[str]:
    """
    返回 root_folder 下的第一层子文件夹列表（仅名称）。若路径非法，抛出异常。
    """
    if not os.path.isdir(root_folder):
        raise FileNotFoundError(f"无效的目录: {root_folder}")
    return [d for d in os.listdir(root_folder) if os.path.isdir(os.path.join(root_folder, d))]


def move_files_with_keyword_in_subfolder(
    root_folder: str,
    keyword: str,
    target_folder: str,
    create_if_not_exists: bool = True,
    recursive: bool = False,
    preview: bool = True
) -> List[str]:
    """
    在 root_folder 下查找所有子文件夹 (或子孙文件夹)：
      - 若文件夹名称包含 keyword，则将其下所有文件移动到 target_folder。
      - preview=True 时，只返回“预览日志”；否则执行实际移动并返回操作日志。
    返回值：日志列表（List[str]）。
    """
    logs: List[str] = []

    # 如果正式执行，需要先创建目标文件夹
    if not preview:
        if create_if_not_exists and not os.path.exists(target_folder):
            try:
                os.makedirs(target_folder, exist_ok=True)
                logs.append(f"[INFO] 已创建目标文件夹: {target_folder}")
            except Exception as e:
                logs.append(f"[ERROR] 创建目标文件夹失败: {e}")
                return logs

    def move_or_preview(file_path: str, dest_folder: str):
        fname = os.path.basename(file_path)
        dest_path = os.path.join(dest_folder, fname)
        if preview:
            logs.append(f"[预览] {file_path} -> {dest_path}")
        else:
            try:
                shutil.move(file_path, dest_path)
                # 修改权限为 777，注意在实际环境下谨慎使用
                os.chmod(dest_path, 0o777)
                os.chmod(dest_folder, 0o777)
                logs.append(f"[移动成功] {file_path} -> {dest_path}")
            except Exception as e:
                logs.append(f"[移动失败] {file_path} -> {dest_path}, 原因: {e}")

    # 遍历逻辑
    if recursive:
        for dirpath, _, filenames in os.walk(root_folder):
            folder_name = os.path.basename(dirpath)
            if keyword in folder_name:
                for file in filenames:
                    src = os.path.join(dirpath, file)
                    if os.path.isfile(src):
                        move_or_preview(src, target_folder)
    else:
        if not os.path.isdir(root_folder):
            logs.append(f"[ERROR] 根目录不存在: {root_folder}")
            return logs
        for name in os.listdir(root_folder):
            subfolder_path = os.path.join(root_folder, name)
            if os.path.isdir(subfolder_path) and keyword in name:
                for file in os.listdir(subfolder_path):
                    src = os.path.join(subfolder_path, file)
                    if os.path.isfile(src):
                        move_or_preview(src, target_folder)

    return logs


def rename_files(
    folder_path: str,
    prefix: str = "NewFile_",
    preview: bool = True,
    custom_pattern: str = "",
    allow_overwrite: bool = False,
) -> List[str]:
    """
    更安全的批量重命名：
    1. 支持自定义正则；若自定义不匹配，则依次使用 DEFAULT_PATTERN_CONFIG。
    2. **预检测重复**：形成重命名映射后，先检查是否出现重复目标文件名，
       或目标文件已存在且不允许覆盖；如发现冲突则记录错误并跳过相应条目。
    3. preview=True 时仅返回预览日志，不执行写操作。

    参数：
      folder_path: 待处理文件夹
      prefix: 新文件名前缀
      preview: 预览模式
      custom_pattern: 自定义提取后缀的正则表达式，应至少含一个捕获组
      allow_overwrite: 是否允许覆盖已存在的同名文件（**默认 False**）

    返回：日志列表
    """
    logs: List[str] = []

    # ---------- 0) 参数校验 ----------
    if not os.path.isdir(folder_path):
        logs.append(f"[ERROR] 文件夹不存在: {folder_path}")
        return logs

    # ---------- 1) 准备匹配规则 ----------
    pattern_config = []
    if custom_pattern.strip():
        try:
            re.compile(custom_pattern.strip())
            pattern_config.append({
                "name": "自定义规则",
                "pattern": custom_pattern.strip(),
                "rename_func": lambda m: m.group(1),
            })
        except re.error as e:
            logs.append(f"[ERROR] 自定义正则无效: {custom_pattern}, 原因: {e}")

    pattern_config.extend(DEFAULT_PATTERN_CONFIG)

    # ---------- 2) 收集文件列表 ----------
    files = [f for f in sorted(os.listdir(folder_path)) if os.path.isfile(os.path.join(folder_path, f))]
    if not files:
        logs.append(f"[INFO] {folder_path} 下没有任何文件")
        return logs

    # ---------- 3) 生成重命名计划 ----------
    rename_pairs: List[Tuple[str, str]] = []  # (old_path, new_path)
    conflicts: List[str] = []
    planned_names: set = set()

    for old_name in files:
        old_path = os.path.join(folder_path, old_name)
        root, ext = os.path.splitext(old_name)

        new_suffix = None
        for rule in pattern_config:
            m = re.search(rule["pattern"], old_name)
            if m:
                new_suffix = rule["rename_func"](m)
                break
        if not new_suffix:
            logs.append(f"[跳过] 文件名不符合任何规则: {old_name}")
            continue

        new_name = f"{prefix}{new_suffix}{ext}"
        new_path = os.path.join(folder_path, new_name)

        # 冲突检测（计划内 + 目标已存在）
        if new_name in planned_names:
            conflicts.append(f"[冲突] 计划内重复目标名: {new_name} (源: {old_name})")
            continue
        if os.path.exists(new_path) and not allow_overwrite and os.path.abspath(new_path) != os.path.abspath(old_path):
            conflicts.append(f"[冲突] 目标已存在: {new_name} (源: {old_name})")
            continue

        planned_names.add(new_name)
        rename_pairs.append((old_path, new_path))

    # ---------- 4) 处理冲突 ----------
    if conflicts:
        logs.extend(conflicts)
        logs.append("[WARN] 检测到以上冲突，相关文件已被跳过。")

    if not rename_pairs:
        logs.append("[INFO] 无可执行的重命名任务")
        return logs

    # ---------- 5) 执行 / 预览 ----------
    if preview:
        logs.append("[预览] 以下文件将被重命名：")
        for old, new in rename_pairs:
            logs.append(f"{os.path.basename(old)} -> {os.path.basename(new)}")
        logs.append("(预览模式，不执行实际重命名)")
    else:
        success, failed = 0, 0
        for old, new in rename_pairs:
            try:
                os.rename(old, new)
                logs.append(f"[已重命名] {os.path.basename(old)} -> {os.path.basename(new)}")
                success += 1
            except Exception as e:
                logs.append(f"[重命名失败] {os.path.basename(old)} -> {os.path.basename(new)}, 原因: {e}")
                failed += 1
        logs.append(f"[SUMMARY] 成功 {success} 个，失败 {failed} 个，跳过 {len(conflicts)} 个。")

    return logs


def delete_empty_folders_with_keyword(
    root_folder: str,
    keyword: str,
    recursive: bool = False,
    preview: bool = True
) -> List[str]:
    """
    在 root_folder 下查找所有“名称含 keyword”的子文件夹，若该文件夹为空则删除。
    preview=True: 只返回预览日志；否则执行删除并返回日志。
    返回：日志列表。
    """
    logs: List[str] = []
    if not os.path.isdir(root_folder):
        logs.append(f"[ERROR] 无效的根目录: {root_folder}")
        return logs

    def try_delete(folder: str):
        if not os.listdir(folder):
            if preview:
                logs.append(f"[预览] 删除空文件夹: {folder}")
            else:
                try:
                    os.rmdir(folder)
                    logs.append(f"[删除成功] {folder}")
                except Exception as e:
                    logs.append(f"[删除失败] {folder}, 原因: {e}")
        else:
            logs.append(f"[跳过] 文件夹不为空: {folder}")

    if recursive:
        for dirpath, dirnames, _ in os.walk(root_folder, topdown=False):
            for d in dirnames:
                if keyword in d:
                    folder_to_check = os.path.join(dirpath, d)
                    try_delete(folder_to_check)
    else:
        for name in os.listdir(root_folder):
            folder_to_check = os.path.join(root_folder, name)
            if os.path.isdir(folder_to_check) and keyword in name:
                try_delete(folder_to_check)

    return logs
