/* ===== Toast Notifications ===== */
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `toast toast--${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

/* ===== Auth: Login ===== */
async function login(e) {
    e.preventDefault();
    const btn = document.getElementById('loginBtn');
    const errorEl = document.getElementById('authError');
    btn.disabled = true;
    btn.textContent = '登录中...';
    errorEl.style.display = 'none';

    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;

    try {
        const res = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password }),
        });
        const data = await res.json();
        if (res.ok && data.success) {
            localStorage.setItem('fs_auth', 'ok');
            localStorage.setItem('fs_user', data.username || username);
            localStorage.setItem('fs_tier', data.tier || 'free');
            if (data.token) localStorage.setItem('fs_token', data.token);
            window.location.href = '/dashboard';
        } else {
            errorEl.textContent = data.detail || '登录失败';
            errorEl.style.display = 'block';
        }
    } catch (err) {
        errorEl.textContent = '网络错误，请稍后重试';
        errorEl.style.display = 'block';
    } finally {
        btn.disabled = false;
        btn.textContent = '登录';
    }
}

/* ===== Auth: Register ===== */
async function register(e) {
    e.preventDefault();
    const btn = document.getElementById('registerBtn');
    const errorEl = document.getElementById('authError');
    btn.disabled = true;
    btn.textContent = '注册中...';
    errorEl.style.display = 'none';

    const username = document.getElementById('username').value.trim();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const password2 = document.getElementById('password2').value;

    if (password !== password2) {
        errorEl.textContent = '两次输入的密码不一致';
        errorEl.style.display = 'block';
        btn.disabled = false;
        btn.textContent = '注册';
        return;
    }

    try {
        const res = await fetch('/api/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password }),
        });
        const data = await res.json();
        if (res.ok && data.success) {
            window.location.href = '/dashboard';
        } else {
            errorEl.textContent = data.detail || '注册失败';
            errorEl.style.display = 'block';
        }
    } catch (err) {
        errorEl.textContent = '网络错误，请稍后重试';
        errorEl.style.display = 'block';
    } finally {
        btn.disabled = false;
        btn.textContent = '注册';
    }
}

/* ===== Auth: Logout ===== */
async function logout() {
    await fetch('/api/logout', { method: 'POST' });
    window.location.href = '/';
}

/* ===== Analyze ===== */
async function analyze(e) {
    e.preventDefault();
    const form = e.target;
    const btn = document.getElementById('analyzeBtn');
    const btnText = btn.querySelector('.btn-text');
    const btnLoading = btn.querySelector('.btn-loading');
    const resultArea = document.getElementById('result');
    const resultContent = document.getElementById('resultContent');
    const resultSources = document.getElementById('resultSources');
    const sourcesList = document.getElementById('sourcesList');

    // Get form data
    const skillType = form.querySelector('[name="skill_type"]').value;
    const queryEl = form.querySelector('[name="query"]');
    const urlEl = form.querySelector('[name="url"]');
    let query = queryEl ? queryEl.value.trim() : '';
    let extraContent = '';

    // For video skill: URL is primary, transcript is optional supplement
    if (skillType === 'video') {
        const url = urlEl ? urlEl.value.trim() : '';
        if (url) {
            extraContent = url;
            if (!query) query = '请拆解分析这个视频内容';
        } else if (!query) {
            showToast('请输入视频链接', 'error');
            return;
        }
    }

    if (!query) {
        showToast('请输入分析内容', 'error');
        return;
    }

    // Show loading with progress steps
    btn.disabled = true;
    btnText.style.display = 'none';
    btnLoading.style.display = '';
    resultArea.style.display = 'none';

    // 创建进度面板
    let progressPanel = document.getElementById('progressPanel');
    if (!progressPanel) {
        progressPanel = document.createElement('div');
        progressPanel.id = 'progressPanel';
        progressPanel.style.cssText = 'margin-top:24px;';
        form.parentNode.insertBefore(progressPanel, form.nextSibling);
    }

    const steps = skillType === 'stock' ? [
        { text: '正在解析股票信息...', time: 0 },
        { text: '正在获取财报数据（东方财富）...', time: 2000 },
        { text: '正在获取资金流向数据...', time: 4000 },
        { text: '正在获取K线行情数据...', time: 5000 },
        { text: '正在搜索最新新闻和研报...', time: 7000 },
        { text: '数据收集完成，AI 正在生成深度分析...', time: 12000 },
        { text: '正在生成投资大师视角分析...', time: 20000 },
        { text: '正在生成情景推演和操作建议...', time: 30000 },
        { text: '报告即将完成，请稍候...', time: 45000 },
    ] : skillType === 'auction' ? [
        { text: '正在获取涨停池数据...', time: 0 },
        { text: '正在获取异动和人气排行...', time: 2000 },
        { text: '数据收集完成，AI 正在生成量化信号...', time: 5000 },
        { text: '正在生成选股策略...', time: 15000 },
        { text: '报告即将完成...', time: 25000 },
    ] : skillType === 'macro' ? [
        { text: '正在获取GDP/CPI/PMI等宏观数据...', time: 0 },
        { text: '正在搜索最新政策动向...', time: 3000 },
        { text: '数据收集完成，AI 正在生成分析...', time: 8000 },
        { text: '报告即将完成...', time: 20000 },
    ] : [
        { text: '正在搜索相关数据...', time: 0 },
        { text: '数据收集完成，AI 正在生成分析...', time: 5000 },
        { text: '报告即将完成，请稍候...', time: 20000 },
    ];

    // 渲染进度面板
    progressPanel.innerHTML = `
        <div class="card" style="padding:24px;">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">
                <div class="loading-spinner" style="border-color:#e5e5e7;border-top-color:#0071e3;width:22px;height:22px;"></div>
                <span id="progressText" style="font-size:0.95rem;color:#1d1d1f;font-weight:500;">${steps[0].text}</span>
            </div>
            <div style="background:#e5e5e7;border-radius:4px;height:4px;overflow:hidden;">
                <div id="progressBar" style="height:100%;background:linear-gradient(90deg,#0071e3,#5856d6);border-radius:4px;width:5%;transition:width 0.5s ease;"></div>
            </div>
            <div style="display:flex;justify-content:space-between;margin-top:8px;">
                <span id="progressStep" style="font-size:0.75rem;color:#86868b;">步骤 1/${steps.length}</span>
                <span id="progressTime" style="font-size:0.75rem;color:#86868b;">已用时 0秒</span>
            </div>
        </div>
    `;
    progressPanel.style.display = '';

    // 动态更新进度
    const startTime = Date.now();
    const stepTimers = [];
    steps.forEach((step, i) => {
        const timer = setTimeout(() => {
            const textEl = document.getElementById('progressText');
            const barEl = document.getElementById('progressBar');
            const stepEl = document.getElementById('progressStep');
            if (textEl) textEl.textContent = step.text;
            if (barEl) barEl.style.width = Math.min(5 + (i + 1) / steps.length * 90, 95) + '%';
            if (stepEl) stepEl.textContent = `步骤 ${i + 1}/${steps.length}`;
        }, step.time);
        stepTimers.push(timer);
    });

    // 计时器
    const timeTimer = setInterval(() => {
        const el = document.getElementById('progressTime');
        if (el) el.textContent = `已用时 ${Math.floor((Date.now() - startTime) / 1000)}秒`;
    }, 1000);

    try {
        // 5分钟超时控制
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 300000);

        console.log('[Finance Suite] 发送分析请求:', skillType, query);

        const res = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                skill_type: skillType,
                query: query,
                extra_content: extraContent,
            }),
            signal: controller.signal,
        });

        clearTimeout(timeoutId);
        console.log('[Finance Suite] 收到响应:', res.status);

        const data = await res.json();
        console.log('[Finance Suite] 解析成功, 结果长度:', data.result?.length || 0);

        if (res.ok && data.success) {
            // 缓存命中提示
            if (data.cached) {
                showToast('命中缓存，秒级返回', 'info');
            }

            // Render markdown to HTML
            if (typeof marked !== 'undefined') {
                resultContent.innerHTML = marked.parse(data.result);
            } else {
                resultContent.innerHTML = '<pre>' + escapeHtml(data.result) + '</pre>';
            }

            // Render sources
            if (data.sources && data.sources.length > 0) {
                sourcesList.innerHTML = data.sources
                    .map((s, i) => `<li>${i + 1}. <a href="${escapeHtml(s.url)}" target="_blank" rel="noopener">${escapeHtml(s.title || s.url)}</a></li>`)
                    .join('');
                resultSources.style.display = '';
            } else {
                resultSources.style.display = 'none';
            }

            // 渲染K线图
            if (data.kline && data.kline.length > 0) {
                const container = document.getElementById('kline-container');
                const chartDiv = document.getElementById('kline-chart');
                if (container && chartDiv) {
                    container.style.display = 'block';
                    chartDiv.innerHTML = ''; // 清空旧图

                    const chart = LightweightCharts.createChart(chartDiv, {
                        width: chartDiv.clientWidth,
                        height: 350,
                        layout: {
                            background: { type: 'solid', color: '#ffffff' },
                            textColor: '#1d1d1f',
                        },
                        grid: {
                            vertLines: { color: '#f0f0f0' },
                            horzLines: { color: '#f0f0f0' },
                        },
                        crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
                        rightPriceScale: { borderColor: '#e5e5e7' },
                        timeScale: { borderColor: '#e5e5e7' },
                    });

                    const candleSeries = chart.addCandlestickSeries({
                        upColor: '#ef4444',      // 中国股市红涨
                        downColor: '#22c55e',    // 绿跌
                        borderUpColor: '#ef4444',
                        borderDownColor: '#22c55e',
                        wickUpColor: '#ef4444',
                        wickDownColor: '#22c55e',
                    });

                    candleSeries.setData(data.kline);

                    // 添加成交量
                    const volumeSeries = chart.addHistogramSeries({
                        priceFormat: { type: 'volume' },
                        priceScaleId: 'volume',
                    });
                    chart.priceScale('volume').applyOptions({
                        scaleMargins: { top: 0.8, bottom: 0 },
                    });
                    volumeSeries.setData(data.kline.map(d => ({
                        time: d.time,
                        value: d.volume,
                        color: d.close >= d.open ? 'rgba(239,68,68,0.3)' : 'rgba(34,197,94,0.3)',
                    })));

                    chart.timeScale().fitContent();

                    // 响应式
                    new ResizeObserver(() => {
                        chart.applyOptions({ width: chartDiv.clientWidth });
                    }).observe(chartDiv);
                }
            }

            resultArea.style.display = '';
            resultArea.scrollIntoView({ behavior: 'smooth', block: 'start' });
        } else {
            showToast(data.detail || '分析失败，请稍后重试', 'error');
        }
    } catch (err) {
        console.error('[Finance Suite] 请求失败:', err.name, err.message);
        if (err.name === 'AbortError') {
            showToast('分析超时（超过5分钟），请稍后重试或简化查询', 'error');
        } else if (err.name === 'TypeError') {
            showToast('网络连接中断，请检查网络后重试', 'error');
        } else {
            showToast('分析失败: ' + (err.message || '未知错误'), 'error');
        }
    } finally {
        // 清理进度
        stepTimers.forEach(t => clearTimeout(t));
        clearInterval(timeTimer);
        const pp = document.getElementById('progressPanel');
        if (pp) pp.style.display = 'none';
        btn.disabled = false;
        btnText.style.display = '';
        btnLoading.style.display = 'none';
    }
}

/* ===== Admin ===== */
async function loadAdminData() {
    try {
        // Load stats
        const statsRes = await fetch('/api/admin/stats');
        if (statsRes.ok) {
            const stats = await statsRes.json();
            document.getElementById('statTotalUsers').textContent = stats.total_users || 0;
            document.getElementById('statTotalAnalyses').textContent = stats.total_analyses || 0;
            document.getElementById('statVipUsers').textContent = stats.vip_users || 0;
            const activeEl = document.getElementById('statActiveToday');
            if (activeEl) activeEl.textContent = '-';
        }

        // Load users
        const usersRes = await fetch('/api/admin/users');
        if (usersRes.ok) {
            const data = await usersRes.json();
            const tbody = document.getElementById('userTableBody');
            if (data.users && data.users.length > 0) {
                tbody.innerHTML = data.users
                    .map(u => `<tr>
                        <td>${u.id}</td>
                        <td>${escapeHtml(u.username)}</td>
                        <td>${escapeHtml(u.email)}</td>
                        <td>
                            <select class="tier-select" onchange="upgradeUser(${u.id}, this.value)">
                                <option value="free" ${u.tier === 'free' ? 'selected' : ''}>Free</option>
                                <option value="vip" ${u.tier === 'vip' ? 'selected' : ''}>VIP</option>
                                <option value="admin" ${u.tier === 'admin' ? 'selected' : ''}>Admin</option>
                            </select>
                        </td>
                        <td>${u.created_at ? new Date(u.created_at).toLocaleDateString('zh-CN') : '-'}</td>
                        <td>-</td>
                    </tr>`)
                    .join('');
            } else {
                tbody.innerHTML = '<tr><td colspan="6" class="table-empty">暂无用户</td></tr>';
            }
        }
    } catch (err) {
        showToast('加载管理数据失败', 'error');
    }
}

async function upgradeUser(userId, tier) {
    try {
        const res = await fetch('/api/admin/upgrade', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId, tier: tier }),
        });
        const data = await res.json();
        if (res.ok && data.success) {
            showToast(data.message, 'success');
        } else {
            showToast(data.detail || '操作失败', 'error');
        }
    } catch (err) {
        showToast('网络错误', 'error');
    }
}

/* ===== Utility ===== */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text || '';
    return div.innerHTML;
}

/* ===== Nav Toggle (Mobile) ===== */
document.addEventListener('DOMContentLoaded', function () {
    const toggle = document.getElementById('navToggle');
    const links = document.getElementById('navLinks');
    if (toggle && links) {
        toggle.addEventListener('click', function () {
            links.classList.toggle('active');
        });
    }
});
