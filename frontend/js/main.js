// frontend/js/main.js

const API_BASE = ''; 
// 如果后端和前端同域部署，这里留空即可；
// 如果后端在  http://localhost:5000 ，则： const API_BASE = 'http://localhost:5000';


/** 辅助：将数组日志逐行追加到指定 <pre> 区域 */
function appendLogs(preId, logs) {
  const pre = document.getElementById(preId);
  pre.textContent = ''; // 清空
  logs.forEach(line => {
    pre.textContent += line + '\n';
  });
}

// —— A) 批量下载 —— 
document.getElementById('btnDownload').addEventListener('click', async () => {
  const linksRaw = document.getElementById('magnetLinks').value.trim();
  const server = document.getElementById('serverAddr').value.trim();
  if (!linksRaw) {
    alert('请先填入至少一行磁力链接');
    return;
  }
  if (!server) {
    alert('请填写服务器地址');
    return;
  }
  const magnet_links = linksRaw.split('\n').map(s => s.trim()).filter(s => s);
  const payload = { magnet_links, server_addr: server };

  appendLogs('logDownload', ['开始请求后端，请稍候...']);
  try {
    const resp = await fetch(API_BASE + '/api/download', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await resp.json();
    if (!data.success) {
      appendLogs('logDownload', [`[ERROR] ${data.error}`]);
    } else {
      appendLogs('logDownload', data.logs);
    }
  } catch (e) {
    appendLogs('logDownload', [`[Exception] ${e}`]);
  }
});

// —— B) 子文件夹预览 —— 
document.getElementById('btnPreviewSub').addEventListener('click', async () => {
  const root = document.getElementById('previewRoot').value.trim();
  if (!root) {
    alert('请填写根目录');
    return;
  }
  appendLogs('logPreviewSub', ['请求中...']);
  try {
    // GET /api/list_subfolders?root_folder=...
    const url = new URL(API_BASE + '/api/list_subfolders', window.location.origin);
    url.searchParams.append('root_folder', root);

    const resp = await fetch(url);
    const data = await resp.json();
    if (!data.success) {
      appendLogs('logPreviewSub', [`[ERROR] ${data.error}`]);
    } else {
      appendLogs('logPreviewSub', ['子文件夹列表：', ...data.subfolders.map(d => '- ' + d)]);
    }
  } catch (e) {
    appendLogs('logPreviewSub', [`[Exception] ${e}`]);
  }
});

// —— C) 按关键字移动文件 —— 
document.getElementById('btnMove').addEventListener('click', async () => {
  const root = document.getElementById('moveRoot').value.trim();
  const keyword = document.getElementById('moveKeyword').value.trim();
  const target = document.getElementById('moveTarget').value.trim();
  const create_if_not_exists = document.getElementById('moveCreate').checked;
  const recursive = document.getElementById('moveRecursive').checked;
  const preview = document.getElementById('movePreview').checked;

  if (!root || !keyword || !target) {
    alert('请填写根目录、关键字和目标文件夹');
    return;
  }
  appendLogs('logMove', ['请求中...']);

  const payload = { root_folder: root, keyword, target_folder: target,
                    create_if_not_exists, recursive, preview };

  try {
    const resp = await fetch(API_BASE + '/api/move_files', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await resp.json();
    if (!data.success) {
      appendLogs('logMove', [`[ERROR] ${data.error}`]);
    } else {
      appendLogs('logMove', data.logs);
    }
  } catch (e) {
    appendLogs('logMove', [`[Exception] ${e}`]);
  }
});

// —— D) 批量重命名 —— 
document.getElementById('btnRename').addEventListener('click', async () => {
  const folder_path = document.getElementById('renameFolder').value.trim();
  const prefix = document.getElementById('renamePrefix').value.trim();
  const custom_pattern = document.getElementById('renamePattern').value.trim();
  const preview = document.getElementById('renamePreview').checked;

  if (!folder_path) {
    alert('请填写要重命名的文件夹路径');
    return;
  }
  appendLogs('logRename', ['请求中...']);

  const payload = { folder_path, prefix, custom_pattern, preview };
  try {
    const resp = await fetch(API_BASE + '/api/rename_files', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await resp.json();
    if (!data.success) {
      appendLogs('logRename', [`[ERROR] ${data.error}`]);
    } else {
      appendLogs('logRename', data.logs);
    }
  } catch (e) {
    appendLogs('logRename', [`[Exception] ${e}`]);
  }
});

// —— E) 删除空文件夹 —— 
document.getElementById('btnDelete').addEventListener('click', async () => {
  const root = document.getElementById('deleteRoot').value.trim();
  const keyword = document.getElementById('deleteKeyword').value.trim();
  const recursive = document.getElementById('deleteRecursive').checked;
  const preview = document.getElementById('deletePreview').checked;

  if (!root || !keyword) {
    alert('请填写根目录和关键字');
    return;
  }
  appendLogs('logDelete', ['请求中...']);

  const payload = { root_folder: root, keyword, recursive, preview };
  try {
    const resp = await fetch(API_BASE + '/api/delete_empty_folders', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await resp.json();
    if (!data.success) {
      appendLogs('logDelete', [`[ERROR] ${data.error}`]);
    } else {
      appendLogs('logDelete', data.logs);
    }
  } catch (e) {
    appendLogs('logDelete', [`[Exception] ${e}`]);
  }
});
