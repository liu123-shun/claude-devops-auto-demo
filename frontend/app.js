// ============================================================
// 图书借阅管理系统 — 共享 JS 工具
// API 基础路径、Token 管理、Fetch 封装、统一侧边栏
// ============================================================

var API_BASE = "";

// ---- Token 管理 ----
function getToken() {
    return localStorage.getItem("token");
}

function setToken(token) {
    localStorage.setItem("token", token);
}

function clearToken() {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
}

function getCurrentUser() {
    var u = localStorage.getItem("user");
    return u ? JSON.parse(u) : null;
}

// ---- HTTP 请求封装 ----
async function apiGet(url) {
    var res = await fetch(API_BASE + url, {
        headers: { Authorization: "Bearer " + getToken() },
    });
    if (res.status === 401) {
        clearToken();
        window.location.href = "/frontend/login.html";
        return null;
    }
    if (res.status === 403) {
        alert("无权限访问");
        return null;
    }
    return res.json();
}

async function apiPost(url, data) {
    var res = await fetch(API_BASE + url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            Authorization: "Bearer " + getToken(),
        },
        body: JSON.stringify(data),
    });
    if (res.status === 401) { clearToken(); window.location.href = "/frontend/login.html"; return null; }
    return res.json();
}

async function apiPut(url, data) {
    var res = await fetch(API_BASE + url, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
            Authorization: "Bearer " + getToken(),
        },
        body: data ? JSON.stringify(data) : undefined,
    });
    if (res.status === 401) { clearToken(); window.location.href = "/frontend/login.html"; return null; }
    return res.json();
}

async function apiDelete(url) {
    var res = await fetch(API_BASE + url, {
        method: "DELETE",
        headers: { Authorization: "Bearer " + getToken() },
    });
    if (res.status === 401) { clearToken(); window.location.href = "/frontend/login.html"; return null; }
    return res.json();
}

// ---- 退出登录 ----
async function logout() {
    var token = getToken();
    if (token) {
        try {
            await fetch("/api/auth/logout", {
                method: "POST",
                headers: { Authorization: "Bearer " + token },
            });
        } catch (e) {}
    }
    clearToken();
    window.location.href = "/frontend/login.html";
}

// ---- 页面鉴权检查 ----
function checkAuth() {
    var token = getToken();
    var user = getCurrentUser();
    if (!token || !user) {
        window.location.href = "/frontend/login.html";
        return null;
    }
    return user;
}

// ---- 显示用户名 ----
function displayUserInfo() {
    var user = getCurrentUser();
    if (user) {
        var el = document.getElementById("display-name");
        if (el) el.textContent = user.name || user.username;
        var el2 = document.getElementById("display-role");
        if (el2) el2.textContent = user.role === "admin" ? "管理员" : "学生";
    }
}

// ---- 弹窗工具 ----
function openModal(id) {
    document.getElementById(id).classList.add("active");
}

function closeModal(id) {
    document.getElementById(id).classList.remove("active");
}

// ---- 分页渲染 ----
function renderPagination(containerId, page, totalPages, onPageClick) {
    var container = document.getElementById(containerId);
    if (!container || totalPages <= 1) {
        if (container) container.innerHTML = "";
        return;
    }
    var html = "";
    html += '<button ' + (page <= 1 ? 'disabled ' : '') + 'data-p="' + (page - 1) + '">«</button>';
    for (var i = 1; i <= totalPages; i++) {
        html += '<button class="' + (i === page ? 'active' : '') + '" data-p="' + i + '">' + i + '</button>';
    }
    html += '<button ' + (page >= totalPages ? 'disabled ' : '') + 'data-p="' + (page + 1) + '">»</button>';
    container.innerHTML = html;
    container.querySelectorAll("button").forEach(function(btn) {
        btn.addEventListener("click", function() {
            var p = parseInt(btn.getAttribute("data-p"));
            if (p >= 1 && p <= totalPages) onPageClick(p);
        });
    });
}

// ---- 统一侧边栏 ----
function renderSidebar(role) {
    var container = document.getElementById("sidebar");
    if (!container) { console.error("sidebar container not found"); return; }

    var path = window.location.pathname;
    var page = path.substring(path.lastIndexOf("/") + 1) || "";

    var menu = [];
    if (role === "admin") {
        menu = [
            { group: "主菜单", items: [
                { href: "admin_index.html", icon: "&#x1F4CA;", label: "首页看板" },
                { href: "admin_charts.html", icon: "&#x1F4C8;", label: "数据可视化" },
            ]},
            { group: "业务管理", items: [
                { href: "admin_book.html", icon: "&#x1F4D6;", label: "图书管理" },
                { href: "admin_reader.html", icon: "&#x1F468;&#x200D;&#x1F393;", label: "学生管理" },
                { href: "admin_announcement.html", icon: "&#x1F4E2;", label: "公告管理" },
            ]},
            { group: "日志审计", items: [
                { href: "admin_login_log.html", icon: "&#x1F4DD;", label: "登录日志" },
                { href: "admin_borrow_log.html", icon: "&#x1F4CB;", label: "借阅日志" },
                { href: "admin_overdue.html", icon: "&#x26A0;&#xFE0F;", label: "逾期图书" },
            ]},
            { group: "系统", items: [
                { href: "admin_settings.html", icon: "&#x2699;&#xFE0F;", label: "系统设置" },
            ]},
        ];
    } else {
        menu = [
            { group: "主菜单", items: [
                { href: "student_index.html", icon: "&#x1F4CA;", label: "我的首页" },
                { href: "student_books.html", icon: "&#x1F4DA;", label: "馆藏浏览" },
            ]},
            { group: "我的记录", items: [
                { href: "student_my_borrow.html", icon: "&#x1F4D6;", label: "我的借阅" },
                { href: "student_stats.html", icon: "&#x1F4C8;", label: "阅读统计" },
                { href: "student_my_login_log.html", icon: "&#x1F4DD;", label: "登录日志" },
            ]},
        ];
    }

    var html = "";
    for (var g = 0; g < menu.length; g++) {
        var group = menu[g];
        html += '<div class="nav-group"><div class="nav-label">' + group.group + '</div>';
        for (var i = 0; i < group.items.length; i++) {
            var item = group.items[i];
            var cls = (page === item.href) ? ' active' : '';
            html += '<a href="' + item.href + '" class="' + cls + '"><span class="icon">' + item.icon + '</span><span>' + item.label + '</span></a>';
        }
        html += '</div>';
    }
    container.innerHTML = html;
}

// ---- 状态标签 ----
function statusTag(status) {
    var map = {
        "borrowed": '<span class="tag tag-yellow">未归还</span>',
        "returned": '<span class="tag tag-green">已归还</span>',
        "overdue": '<span class="tag tag-red">逾期</span>',
    };
    return map[status] || status;
}

// ---- CSV 导出工具 ----
function escapeCSV(val) {
    if (val === null || val === undefined) return "";
    var s = String(val).replace(/\n/g, " ").replace(/\r/g, "");
    if (s.indexOf(",") !== -1 || s.indexOf('"') !== -1 || s.indexOf("\n") !== -1) {
        s = '"' + s.replace(/"/g, '""') + '"';
    }
    return s;
}

function exportCSV(filename, headers, rows) {
    var bom = "﻿";
    var csv = bom + headers.map(escapeCSV).join(",") + "\n";
    for (var i = 0; i < rows.length; i++) {
        csv += rows[i].map(escapeCSV).join(",") + "\n";
    }
    var blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = filename + "_" + new Date().toISOString().slice(0, 10) + ".csv";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}
