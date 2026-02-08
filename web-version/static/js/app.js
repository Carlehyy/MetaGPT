/**
 * AI虚拟软件公司 - 主应用脚本
 * 功能：WebSocket通信、消息渲染、主题切换、提及功能
 */

// ===== 配置 =====
const CONFIG = {
    WS_URL: 'ws://38.14.254.160:8000/ws/boss',
    RECONNECT_INTERVAL: 3000,
    MAX_RECONNECT_ATTEMPTS: 5
};

// ===== 角色定义 =====
const ROLES = {
    boss: {
        id: 'boss',
        name: '老板',
        emoji: '👔',
        color: '#8b5cf6',
        bgColor: 'bg-purple-100 dark:bg-purple-900',
        textColor: 'text-purple-700 dark:text-purple-300',
        description: '项目决策者'
    },
    pm: {
        id: 'pm',
        name: '产品经理',
        emoji: '📊',
        color: '#f59e0b',
        bgColor: 'bg-amber-100 dark:bg-amber-900',
        textColor: 'text-amber-700 dark:text-amber-300',
        description: '需求分析与规划'
    },
    architect: {
        id: 'architect',
        name: '架构师',
        emoji: '🏗️',
        color: '#10b981',
        bgColor: 'bg-emerald-100 dark:bg-emerald-900',
        textColor: 'text-emerald-700 dark:text-emerald-300',
        description: '系统架构设计'
    },
    designer: {
        id: 'designer',
        name: '产品设计师',
        emoji: '🎨',
        color: '#ec4899',
        bgColor: 'bg-pink-100 dark:bg-pink-900',
        textColor: 'text-pink-700 dark:text-pink-300',
        description: 'UI/UX设计'
    },
    pjm: {
        id: 'pjm',
        name: '项目经理',
        emoji: '📋',
        color: '#06b6d4',
        bgColor: 'bg-cyan-100 dark:bg-cyan-900',
        textColor: 'text-cyan-700 dark:text-cyan-300',
        description: '项目进度管理'
    },
    engineer: {
        id: 'engineer',
        name: '开发工程师',
        emoji: '💻',
        color: '#6366f1',
        bgColor: 'bg-indigo-100 dark:bg-indigo-900',
        textColor: 'text-indigo-700 dark:text-indigo-300',
        description: '代码开发实现'
    },
    qa: {
        id: 'qa',
        name: '测试工程师',
        emoji: '🧪',
        color: '#f97316',
        bgColor: 'bg-orange-100 dark:bg-orange-900',
        textColor: 'text-orange-700 dark:text-orange-300',
        description: '质量保证测试'
    },
    devops: {
        id: 'devops',
        name: '运维工程师',
        emoji: '🚀',
        color: '#14b8a6',
        bgColor: 'bg-teal-100 dark:bg-teal-900',
        textColor: 'text-teal-700 dark:text-teal-300',
        description: '部署与运维'
    }
};

// ===== 开发阶段定义 =====
const PHASES = [
    { id: 'P1', name: '需求分析', description: '产品经理收集和分析需求', icon: '📝' },
    { id: 'P2', name: '架构设计', description: '架构师设计系统架构', icon: '🏗️' },
    { id: 'P3', name: '产品设计', description: '设计师完成UI/UX设计', icon: '🎨' },
    { id: 'P4', name: '项目规划', description: '项目经理制定开发计划', icon: '📋' },
    { id: 'P5', name: '开发实现', description: '工程师进行代码开发', icon: '💻' },
    { id: 'P6', name: '代码审查', description: '团队进行代码Review', icon: '🔍' },
    { id: 'P7', name: '测试验证', description: '测试工程师执行测试', icon: '🧪' },
    { id: 'P8', name: '部署上线', description: '运维工程师部署发布', icon: '🚀' },
    { id: 'P9', name: '项目交付', description: '项目完成并交付', icon: '✅' }
];

// ===== 应用状态 =====
const state = {
    currentPhase: 0,
    messages: [],
    ws: null,
    reconnectAttempts: 0,
    isTyping: false,
    theme: localStorage.getItem('theme') || 'light',
    userRole: 'boss'
};

// ===== DOM 元素 =====
const elements = {
    phaseNav: document.getElementById('phase-nav'),
    roleList: document.getElementById('role-list'),
    messageList: document.getElementById('message-list'),
    chatContainer: document.getElementById('chat-container'),
    messageInput: document.getElementById('message-input'),
    sendBtn: document.getElementById('send-btn'),
    themeToggle: document.getElementById('theme-toggle'),
    mentionPopup: document.getElementById('mention-popup'),
    currentPhaseTitle: document.getElementById('current-phase-title'),
    currentPhaseDesc: document.getElementById('current-phase-desc'),
    currentPhaseBadge: document.getElementById('current-phase-badge'),
    overallProgress: document.getElementById('overall-progress'),
    progressBar: document.getElementById('progress-bar')
};

// ===== 初始化 =====
function init() {
    initTheme();
    renderPhaseNav();
    renderRoleList();
    initWebSocket();
    initEventListeners();
    loadMockMessages();
    updateProgress();
}

// ===== 主题管理 =====
function initTheme() {
    if (state.theme === 'dark' || (!state.theme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.documentElement.classList.add('dark');
        state.theme = 'dark';
    } else {
        document.documentElement.classList.remove('dark');
        state.theme = 'light';
    }
}

function toggleTheme() {
    state.theme = state.theme === 'light' ? 'dark' : 'light';
    document.documentElement.classList.toggle('dark');
    localStorage.setItem('theme', state.theme);
}

// ===== 阶段导航渲染 =====
function renderPhaseNav() {
    elements.phaseNav.innerHTML = PHASES.map((phase, index) => `
        <div class="phase-item flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-pointer ${index === state.currentPhase ? 'active' : ''} ${index < state.currentPhase ? 'completed' : ''}"
             onclick="setPhase(${index})">
            <div class="phase-number ${index === state.currentPhase ? 'bg-primary-500 text-white' : index < state.currentPhase ? '' : 'bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400'}">
                ${index < state.currentPhase ? '✓' : phase.id}
            </div>
            <div class="phase-text flex-1 min-w-0">
                <div class="text-sm font-medium truncate ${index === state.currentPhase ? 'text-primary-700 dark:text-primary-400' : 'text-gray-700 dark:text-gray-300'}">${phase.name}</div>
                <div class="text-xs text-gray-400 truncate">${phase.description}</div>
            </div>
        </div>
    `).join('');
}

function setPhase(index) {
    state.currentPhase = index;
    renderPhaseNav();
    updatePhaseInfo();
    updateProgress();
    
    // 添加阶段切换的系统消息
    addSystemMessage(`进入${PHASES[index].name}阶段`);
}

function updatePhaseInfo() {
    const phase = PHASES[state.currentPhase];
    elements.currentPhaseTitle.textContent = phase.name;
    elements.currentPhaseDesc.textContent = phase.description;
    elements.currentPhaseBadge.textContent = phase.id;
}

function updateProgress() {
    const progress = Math.round(((state.currentPhase + 1) / PHASES.length) * 100);
    elements.overallProgress.textContent = `${progress}%`;
    elements.progressBar.style.width = `${progress}%`;
}

// ===== 角色列表渲染 =====
function renderRoleList() {
    elements.roleList.innerHTML = Object.values(ROLES).map(role => `
        <div class="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors cursor-pointer"
             onclick="mentionRole('${role.id}')">
            <div class="role-avatar ${role.bgColor} online" style="color: ${role.color}">
                ${role.emoji}
            </div>
            <div class="flex-1 min-w-0">
                <div class="text-sm font-medium text-gray-900 dark:text-gray-100">${role.name}</div>
                <div class="text-xs text-gray-500 dark:text-gray-400 truncate">${role.description}</div>
            </div>
            <div class="w-2 h-2 rounded-full" style="background-color: ${role.color}"></div>
        </div>
    `).join('');
}

// ===== 消息渲染 =====
function renderMessage(message) {
    const role = ROLES[message.roleId] || ROLES.boss;
    const isMe = message.roleId === state.userRole;
    const hasMention = message.content.includes('@老板');
    
    const messageHtml = `
        <div class="message-bubble flex gap-4 ${isMe ? 'flex-row-reverse' : ''} ${hasMention ? 'mention-boss p-3 rounded-xl' : ''}" data-message-id="${message.id}">
            <div class="flex-shrink-0">
                <div class="role-avatar ${role.bgColor} online cursor-pointer" 
                     style="color: ${role.color}"
                     onclick="mentionRole('${role.id}')"
                     title="${role.name}">
                    ${role.emoji}
                </div>
            </div>
            <div class="flex-1 ${isMe ? 'text-right' : ''}">
                <div class="flex items-center gap-2 ${isMe ? 'justify-end' : ''} mb-1">
                    <span class="font-medium text-sm" style="color: ${role.color}">${role.name}</span>
                    <span class="text-xs text-gray-400">${formatTime(message.timestamp)}</span>
                </div>
                <div class="message-content inline-block max-w-full text-left">
                    <div class="px-4 py-3 rounded-2xl ${isMe ? 'bg-primary-500 text-white' : 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700'} shadow-sm">
                        ${formatMessageContent(message.content)}
                    </div>
                </div>
            </div>
        </div>
    `;
    
    return messageHtml;
}

function formatMessageContent(content) {
    // 处理提及
    content = content.replace(/@老板/g, '<span class="mention-boss-highlight">@老板</span>');
    content = content.replace(/@([^\s]+)/g, '<span class="mention-highlight">@$1</span>');
    
    // 处理换行
    content = content.replace(/\n/g, '<br>');
    
    // 处理代码块
    content = content.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
    
    // 处理行内代码
    content = content.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // 处理链接
    content = content.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');
    
    return content;
}

function formatTime(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) return '刚刚';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`;
    
    return date.toLocaleString('zh-CN', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function addMessage(message) {
    state.messages.push(message);
    const messageHtml = renderMessage(message);
    elements.messageList.insertAdjacentHTML('beforeend', messageHtml);
    scrollToBottom();
}

function addSystemMessage(content) {
    const systemHtml = `
        <div class="system-message">
            <div class="system-message-content">
                ${content}
            </div>
        </div>
    `;
    elements.messageList.insertAdjacentHTML('beforeend', systemHtml);
    scrollToBottom();
}

function scrollToBottom() {
    elements.chatContainer.scrollTop = elements.chatContainer.scrollHeight;
}

// ===== 加载模拟消息 =====
function loadMockMessages() {
    const mockMessages = [
        {
            id: 1,
            roleId: 'pm',
            content: '大家好！我们开始新项目的需求分析阶段。首先我来介绍一下项目背景和目标。',
            timestamp: Date.now() - 3600000
        },
        {
            id: 2,
            roleId: 'architect',
            content: '@产品经理 收到！我已经准备好技术方案了。请分享详细需求文档。',
            timestamp: Date.now() - 3000000
        },
        {
            id: 3,
            roleId: 'boss',
            content: '各位，这个项目时间比较紧，希望大家高效协作。有任何问题随时@我。',
            timestamp: Date.now() - 2400000
        },
        {
            id: 4,
            roleId: 'designer',
            content: '我已经开始准备设计规范了。等需求确定后就可以开始UI设计。',
            timestamp: Date.now() - 1800000
        },
        {
            id: 5,
            roleId: 'pjm',
            content: '我来制定项目计划。预计P1阶段需要3天，P2-P4各2天，P5开发阶段需要10天。',
            timestamp: Date.now() - 1200000
        },
        {
            id: 6,
            roleId: 'engineer',
            content: '技术栈建议用React + TypeScript + Tailwind CSS，后端用Python FastAPI。',
            timestamp: Date.now() - 600000
        },
        {
            id: 7,
            roleId: 'qa',
            content: '我会准备测试计划和测试用例模板，确保项目质量。',
            timestamp: Date.now() - 300000
        },
        {
            id: 8,
            roleId: 'devops',
            content: 'CI/CD流水线已经配置好了，支持自动化构建和部署。',
            timestamp: Date.now() - 60000
        }
    ];
    
    mockMessages.forEach(msg => addMessage(msg));
}

// ===== WebSocket 连接 =====
function initWebSocket() {
    try {
        state.ws = new WebSocket(CONFIG.WS_URL);
        
        state.ws.onopen = () => {
            console.log('WebSocket connected');
            state.reconnectAttempts = 0;
            showConnectionStatus('connected');
        };
        
        state.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            handleWebSocketMessage(data);
        };
        
        state.ws.onclose = () => {
            console.log('WebSocket disconnected');
            showConnectionStatus('disconnected');
            attemptReconnect();
        };
        
        state.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            showConnectionStatus('disconnected');
        };
    } catch (error) {
        console.error('WebSocket initialization error:', error);
        showConnectionStatus('disconnected');
    }
}

function handleWebSocketMessage(data) {
    console.log('收到WebSocket消息:', data);
    switch (data.type) {
        case 'boss_message':
            // 老板消息确认
            console.log('老板消息已发送');
            break;
        case 'ai_message':
            // AI角色消息
            if (data.data) {
                const msg = {
                    id: data.data.id || Date.now(),
                    roleId: data.data.role || 'assistant',
                    content: data.data.content || '',
                    timestamp: data.data.timestamp || Date.now()
                };
                addMessage(msg);
            }
            break;
        case 'message':
            addMessage(data.payload || data.data);
            break;
        case 'typing':
            showTypingIndicator((data.payload || data.data).roleId);
            break;
        case 'phase_change':
            setPhase((data.payload || data.data).phaseIndex);
            break;
        case 'system':
            addSystemMessage((data.payload || data.data).message || (data.payload || data.data).content);
            break;
        default:
            console.log('未知消息类型:', data.type);
    }
}

function attemptReconnect() {
    if (state.reconnectAttempts < CONFIG.MAX_RECONNECT_ATTEMPTS) {
        state.reconnectAttempts++;
        showConnectionStatus('connecting');
        setTimeout(() => {
            console.log(`Reconnecting... attempt ${state.reconnectAttempts}`);
            initWebSocket();
        }, CONFIG.RECONNECT_INTERVAL);
    }
}

function sendMessage(content) {
    if (!content.trim()) return;
    
    const message = {
        id: Date.now(),
        roleId: state.userRole,
        content: content.trim(),
        timestamp: Date.now()
    };
    
    // 本地显示
    addMessage(message);
    
    // 发送到服务器
    if (state.ws && state.ws.readyState === WebSocket.OPEN) {
        state.ws.send(JSON.stringify({
            type: 'boss_message',
            data: { content: content.trim(), timestamp: Date.now() }
        }));
    }
    
    // 清空输入框
    elements.messageInput.value = '';
    elements.messageInput.style.height = 'auto';
}

function showConnectionStatus(status) {
    // 移除现有状态指示器
    const existing = document.querySelector('.connection-status');
    if (existing) existing.remove();
    
    const statusMap = {
        connected: { text: '已连接', class: 'connected' },
        disconnected: { text: '已断开', class: 'disconnected' },
        connecting: { text: '连接中...', class: 'connecting' }
    };
    
    const statusInfo = statusMap[status];
    const indicator = document.createElement('div');
    indicator.className = `connection-status ${statusInfo.class}`;
    indicator.textContent = statusInfo.text;
    document.body.appendChild(indicator);
    
    if (status === 'connected') {
        setTimeout(() => indicator.remove(), 3000);
    }
}

// ===== 提及功能 =====
function mentionRole(roleId) {
    const role = ROLES[roleId];
    if (!role) return;
    
    const input = elements.messageInput;
    const mention = `@${role.name} `;
    
    const start = input.selectionStart;
    const end = input.selectionEnd;
    const value = input.value;
    
    input.value = value.substring(0, start) + mention + value.substring(end);
    input.focus();
    input.setSelectionRange(start + mention.length, start + mention.length);
}

function showMentionPopup() {
    const popup = elements.mentionPopup;
    const input = elements.messageInput;
    const rect = input.getBoundingClientRect();
    
    popup.style.left = `${rect.left}px`;
    popup.style.top = `${rect.top - 200}px`;
    popup.classList.remove('hidden');
    
    popup.innerHTML = Object.values(ROLES).map((role, index) => `
        <div class="mention-option ${index === 0 ? 'selected' : ''}" data-role-id="${role.id}">
            <span>${role.emoji}</span>
            <span>${role.name}</span>
        </div>
    `).join('');
    
    // 添加点击事件
    popup.querySelectorAll('.mention-option').forEach(option => {
        option.addEventListener('click', () => {
            mentionRole(option.dataset.roleId);
            hideMentionPopup();
        });
    });
}

function hideMentionPopup() {
    elements.mentionPopup.classList.add('hidden');
}

// ===== 打字指示器 =====
function showTypingIndicator(roleId) {
    const role = ROLES[roleId];
    if (!role) return;
    
    const existing = document.querySelector('.typing-indicator-container');
    if (existing) existing.remove();
    
    const typingHtml = `
        <div class="typing-indicator-container flex gap-4 mt-4" data-role-id="${roleId}">
            <div class="flex-shrink-0">
                <div class="role-avatar ${role.bgColor}" style="color: ${role.color}">
                    ${role.emoji}
                </div>
            </div>
            <div class="flex-1">
                <div class="text-sm mb-1" style="color: ${role.color}">${role.name}</div>
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        </div>
    `;
    
    elements.messageList.insertAdjacentHTML('beforeend', typingHtml);
    scrollToBottom();
    
    // 3秒后移除
    setTimeout(() => {
        const indicator = document.querySelector(`.typing-indicator-container[data-role-id="${roleId}"]`);
        if (indicator) indicator.remove();
    }, 3000);
}

// ===== 事件监听 =====
function initEventListeners() {
    // 主题切换
    elements.themeToggle.addEventListener('click', toggleTheme);
    
    // 发送消息
    elements.sendBtn.addEventListener('click', () => {
        sendMessage(elements.messageInput.value);
    });
    
    // 回车发送
    elements.messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage(elements.messageInput.value);
        }
    });
    
    // 输入框自动高度
    elements.messageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 120) + 'px';
        
        // 检测@符号
        if (this.value.endsWith('@')) {
            showMentionPopup();
        } else {
            hideMentionPopup();
        }
    });
    
    // 点击外部关闭提及弹窗
    document.addEventListener('click', (e) => {
        if (!elements.mentionPopup.contains(e.target) && e.target !== elements.messageInput) {
            hideMentionPopup();
        }
    });
    
    // 滚动加载更多消息
    elements.chatContainer.addEventListener('scroll', () => {
        if (elements.chatContainer.scrollTop === 0) {
            // 可以在这里加载历史消息
            console.log('Load more messages...');
        }
    });
}

// ===== 模拟实时消息（演示用） =====
function simulateIncomingMessage() {
    const roleIds = Object.keys(ROLES).filter(id => id !== 'boss');
    const randomRole = roleIds[Math.floor(Math.random() * roleIds.length)];
    
    const responses = [
        '收到，我来处理这个问题。',
        '好的，我会尽快完成。',
        '这个方案我觉得可行。',
        '@老板 请您确认一下这个需求。',
        '我已经更新了文档，大家看一下。',
        '代码已提交，等待Review。',
        '测试用例已经准备好了。',
        '部署环境已配置完成。'
    ];
    
    const message = {
        id: Date.now(),
        roleId: randomRole,
        content: responses[Math.floor(Math.random() * responses.length)],
        timestamp: Date.now()
    };
    
    addMessage(message);
}

// 每30秒模拟一条新消息（演示用）
// setInterval(simulateIncomingMessage, 30000);

// ===== 启动应用 =====
document.addEventListener('DOMContentLoaded', init);

// ===== 导出全局函数（供HTML调用） =====
window.setPhase = setPhase;
window.mentionRole = mentionRole;
