/* ============================================================
   图书借阅管理系统 — 共享 JS 工具
   API 基础路径、Token 管理、Fetch 封装
   ============================================================ */

const API_BASE = "";

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
    const u = localStorage.getItem("user");
    return u ? JSON.parse(u) : null;
}

// ---- HTTP 请求封装 ----
async function apiGet(url) {
    const res = await fetch(API_BASE + url, {
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
    const res = await fetch(API_BASE + url, {
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
    const res = await fetch(API_BASE + url, {
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
    const res = await fetch(API_BASE + url, {
        method: "DELETE",
        headers: { Authorization: "Bearer " + getToken() },
    });
    if (res.status === 401) { clearToken(); window.location.href = "/frontend/login.html"; return null; }
    return res.json();
}

// ---- 退出登录 ----
async function logout() {
    // 先调后端接口写入 logout_time
    const token = getToken();
    if (token) {
        try {
            await fetch("/api/auth/logout", {
                method: "POST",
                headers: { Authorization: "Bearer " + token },
            });
        } catch (e) {
            // 即使接口异常也继续清理本地
        }
    }
    clearToken();
    window.location.href = "/frontend/login.html";
}

// ---- 页面鉴权检查 ----
function checkAuth() {
    const token = getToken();
    const user = getCurrentUser();
    if (!token || !user) {
        window.location.href = "/frontend/login.html";
        return null;
    }
    return user;
}

// ---- 显示用户名 ----
function displayUserInfo() {
    const user = getCurrentUser();
    if (user) {
        const el = document.getElementById("display-name");
        if (el) el.textContent = user.name || user.username;
        const el2 = document.getElementById("display-role");
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
    const container = document.getElementById(containerId);
    if (!container || totalPages <= 1) {
        if (container) container.innerHTML = "";
        return;
    }
    let html = "";
    html += `<button ${page <= 1 ? "disabled" : ""} onclick="void(0)" data-p="${page - 1}">&laquo;</button>`;
    for (let i = 1; i <= totalPages; i++) {
        html += `<button class="${i === page ? 'active' : ''}" data-p="${i}">${i}</button>`;
    }
    html += `<button ${page >= totalPages ? "disabled" : ""} data-p="${page + 1}">&raquo;</button>`;
    container.innerHTML = html;
    container.querySelectorAll("button").forEach(btn => {
        btn.addEventListener("click", () => {
            const p = parseInt(btn.getAttribute("data-p"));
            if (p >= 1 && p <= totalPages) onPageClick(p);
        });
    });
}

// ---- 统一侧边栏渲染（所有页面共享同一份模板，杜绝跳变） ----
function renderSidebar(role) {
    const container = document.getElementById("sidebar");
    if (!container) return;
    const page = window.location.pathname.split("/").pop() || "";

    // 管理员侧边栏模板
    const adminMenu = [
        { group: "主菜单", items: [
            { href: "admin_index.html", icon: "📊", label: "首页看板" },
            { href: "admin_charts.html", icon: "📈", label: "数据可视化" },
        ]},
        { group: "业务管理", items: [
            { href: "admin_book.html", icon: "📖", label: "图书管理" },
            { href: "admin_reader.html", icon: "👨‍🎓", label: "学生管理" },
            { href: "admin_announcement.html", icon: "📢", label: "公告管理" },
        ]},
        { group: "日志审计", items: [
            { href: "admin_login_log.html", icon: "📝", label: "登录日志" },
            { href: "admin_borrow_log.html", icon: "📋", label: "借阅日志" },
            { href: "admin_overdue.html", icon: "⚠️", label: "逾期图书" },
        ]},
    ];

    // 学生侧边栏模板
    const studentMenu = [
        { group: "主菜单", items: [
            { href: "student_index.html", icon: "📊", label: "我的首页" },
            { href: "student_books.html", icon: "📚", label: "馆藏浏览" },
        ]},
        { group: "我的记录", items: [
            { href: "student_my_borrow.html", icon: "📖", label: "我的借阅" },
            { href: "student_stats.html", icon: "📈", label: "阅读统计" },
            { href: "student_my_login_log.html", icon: "📝", label: "登录日志" },
        ]},
    ];

    const menu = role === "admin" ? adminMenu : studentMenu;

    let html = "";
    for (const g of menu) {
        html += `<div class="nav-group"><div class="nav-label">${g.group}</div>`;
        for (const item of g.items) {
            const isActive = page === item.href ? " active" : "";
            html += `<a href="${item.href}" class="${isActive.trim()}"><span class="icon">${item.icon}</span><span>${item.label}</span></a>`;
        }
        html += "</div>";
    }
    container.innerHTML = html;
}

// ---- 状态标签 ----
function statusTag(status) {
    const map = {
        "borrowed": '<span class="tag tag-yellow">未归还</span>',
        "returned": '<span class="tag tag-green">已归还</span>',
        "overdue": '<span class="tag tag-red">逾期</span>',
    };
    return map[status] || status;
}
