// ======= Tab切换 =======
const tabs = [
    {btn:'tab-student', section:'section-student', load:loadStudents},
    {btn:'tab-award', section:'section-award', load:loadAwards},
    {btn:'tab-check', section:'section-check', load:loadChecks},
    {btn:'tab-visitor', section:'section-visitor', load:loadVisitors},
    {btn:'tab-stats', section:'section-stats', load:()=>loadStatsCharts('occupancy')},
    {btn:'tab-bed', section:'section-bed', load:loadBedList}
];
tabs.forEach((t, i) => {
    document.getElementById(t.btn).onclick = () => {
        tabs.forEach((tt, j) => {
            document.getElementById(tt.btn).classList.toggle('active', i===j);
            document.getElementById(tt.section).classList.toggle('active', i===j);
        });
        t.load();
        // ==== 修复ECharts在Tab切换后图表变小的问题 ====
        if(t.section === 'section-stats') {
            setTimeout(() => {
                if (window.occupancyChart) window.occupancyChart.resize();
                if (window.awardChart) window.awardChart.resize();
                if (window.visitorChart) window.visitorChart.resize();
            }, 20);
        }
    }
});

// ======= 学生管理 =======
let stPage = 1, stTotal = 0, stPerPage = 100;
let filterUngraduated = true;

// 获取筛选参数
function getStudentFilters() {
    return {
        student_no: document.getElementById('filter-student-no')?.value.trim(),
        name: document.getElementById('filter-name')?.value.trim(),
        gender: document.getElementById('filter-gender')?.value,
        grade: document.getElementById('filter-grade')?.value.trim(),
        phone: document.getElementById('filter-phone')?.value.trim(),
        dorm_building: document.getElementById('filter-dorm-building')?.value.trim(),
        dorm_room_number: document.getElementById('filter-dorm-room')?.value.trim(),
        bed_number: document.getElementById('filter-bed-number')?.value.trim()
    };
}

function loadStudents(page=1) {
    stPage = page;
    let url = `/api/admin/students?page=${page}&per_page=${stPerPage}`;
    if (filterUngraduated) url += '&graduated=0';
    // 拼接筛选参数
    const filters = getStudentFilters();
    Object.keys(filters).forEach(k => {
        if (filters[k]) url += `&${k}=${encodeURIComponent(filters[k])}`;
    });
    fetch(url).then(r=>r.json()).then(res=>{
        const data = res.data || [];
        stTotal = res.total || 0;
        let tb='';
        data.forEach(s=>{
            tb+=`<tr>
                <td>${s.student_no}</td>
                <td>${s.name}</td>
                <td>${s.gender==='M'?'男':'女'}</td>
                <td>${s.grade||''}</td>
                <td>${s.phone||''}</td>
                <td>${(s.dorm_building && s.dorm_room_number) ? (s.dorm_building + '-' + s.dorm_room_number) : ''}</td>
                <td>${s.bed_number||''}</td>
                <td>${s.remark||''}</td>
                <td>
                    <button type="button" onclick="editStudent(${s.id})">编辑</button>
                    <button type="button" onclick="deleteStudent(${s.id})">删除</button>
                </td>
            </tr>`;
        });
        document.getElementById('student-tbody').innerHTML = tb;
        renderStudentPagination();
    });
}
function renderStudentPagination() {
    const totalPages = Math.ceil(stTotal / stPerPage);
    let html = '';
    if (totalPages > 1) {
        html += `<button type="button" ${stPage===1?'disabled':''} onclick="loadStudents(${stPage-1})">上一页</button>`;
        let start = Math.max(1, stPage-2), end = Math.min(totalPages, stPage+2);
        if (start > 1) html += `<span>...</span>`;
        for(let i=start;i<=end;i++){
            html += `<button type="button" ${i===stPage?'style="font-weight:bold"':''} onclick="loadStudents(${i})">${i}</button>`;
        }
        if (end < totalPages) html += `<span>...</span>`;
        html += `<button type="button" ${stPage===totalPages?'disabled':''} onclick="loadStudents(${stPage+1})">下一页</button>`;
    }
    document.getElementById('student-pagination').innerHTML = html;
}
document.getElementById('add-student-btn').onclick = () => showStudentModal('add');
document.getElementById('filter-ungraduated-btn').onclick = function() {
    filterUngraduated = !filterUngraduated;
    this.textContent = filterUngraduated ? '显示全部学生' : '只看未毕业学生';
    loadStudents(1);
};
filterUngraduated = true;
document.getElementById('filter-ungraduated-btn').textContent = '显示全部学生';
loadStudents();

// 筛选栏按钮绑定
document.getElementById('filter-student-btn').onclick = function() {
    loadStudents(1);
};
document.getElementById('reset-student-filter-btn').onclick = function() {
    document.getElementById('filter-student-no').value = '';
    document.getElementById('filter-name').value = '';
    document.getElementById('filter-gender').value = '';
    document.getElementById('filter-grade').value = '';
    document.getElementById('filter-phone').value = '';
    document.getElementById('filter-dorm-building').value = '';
    document.getElementById('filter-dorm-room').value = '';
    document.getElementById('filter-bed-number').value = '';
    loadStudents(1);
};
window.editStudent = function(id) {
    fetch(`/api/admin/students/${id}`).then(r=>r.json()).then(res=>{
        if(res.success) showStudentModal('edit', res.data);
        else alert('获取数据失败');
    });
};
window.deleteStudent = function(id) {
    if(confirm('确定要删除该学生吗？')) {
        fetch(`/api/admin/students/${id}`, {method:'DELETE'})
        .then(r=>r.json())
        .then(res=>{
            if(res.success) { loadStudents(stPage); alert('删除成功'); }
            else alert(res.message || '删除失败');
        });
    }
};
function showStudentModal(type, s) {
    document.getElementById('modal-bg').style.display = 'block';
    document.getElementById('modal').style.display = 'block';
    document.getElementById('modal-title').textContent = type==='add'?'新增学生':'编辑学生';
    const form = document.getElementById('modal-form');
    form.innerHTML = `
    <div style="margin-bottom:13px"><label>学号：<input type="text" id="st-student_no" required style="width:200px"></label></div>
    <div style="margin-bottom:13px"><label>姓名：<input type="text" id="st-name" required style="width:200px"></label></div>
    <div style="margin-bottom:13px"><label>性别：<select id="st-gender" style="width:80px"><option value="M">男</option><option value="F">女</option></select></label></div>
    <div style="margin-bottom:13px"><label>年级：<input type="number" id="st-grade" required style="width:200px" min="1900" max="2099"></label></div>
    <div style="margin-bottom:13px"><label>电话：<input type="text" id="st-phone" style="width:200px"></label></div>
    <div style="margin-bottom:13px">
        <label>宿舍楼：
            <select id="st-dorm_building" style="width:90px">
                <option value="">请选择</option>
                <option value="A">A</option>
                <option value="B">B</option>
                <option value="C">C</option>
                <option value="D">D</option>
                <option value="E">E</option>
                <option value="F">F</option>
                <option value="G">G</option>
                <option value="H">H</option>
                <option value="I">I</option>
                <option value="J">J</option>
                <option value="K">K</option>
                <option value="L">L</option>
                <option value="M">M</option>
            </select>
        </label>
    </div>
    <div style="margin-bottom:13px">
        <label>房间号：<input type="text" id="st-dorm_room_number" style="width:60px"></label>
        <label>床号：
            <select id="st-bed_number" style="width:60px">
                <option value="">请选择</option>
                <option value="1">1</option>
                <option value="2">2</option>
                <option value="3">3</option>
                <option value="4">4</option>
            </select>
        </label>
    </div>
    <div style="margin-bottom:13px"><label>备注：<input type="text" id="st-remark" style="width:200px"></label></div>
    <div style="text-align:right;margin-top:20px;">
        <button type="button" id="modal-cancel">取消</button>
        <button type="submit" id="modal-ok">确定</button>
    </div>
    `;
    if(type==='edit' && s) {
        document.getElementById('st-student_no').value = s.student_no;
        document.getElementById('st-name').value = s.name;
        document.getElementById('st-gender').value = s.gender;
        document.getElementById('st-grade').value = s.grade;
        document.getElementById('st-phone').value = s.phone||'';
        document.getElementById('st-dorm_building').value = s.dorm_building||'';
        document.getElementById('st-dorm_room_number').value = s.dorm_room_number||'';
        document.getElementById('st-bed_number').value = s.bed_number||'';
        document.getElementById('st-remark').value = s.remark||'';
        form.dataset.editId = s.id;
    } else {
        form.dataset.editId = '';
    }
    form.onsubmit = null;
    document.getElementById('modal-cancel').onclick = closeModal;
    document.getElementById('modal-bg').onclick = closeModal;
    form.onsubmit = function(e) {
        e.preventDefault();
        const id = form.dataset.editId;
        const sd = {
            student_no: document.getElementById('st-student_no').value.trim(),
            name: document.getElementById('st-name').value.trim(),
            gender: document.getElementById('st-gender').value,
            grade: document.getElementById('st-grade').value,
            phone: document.getElementById('st-phone').value.trim(),
            dorm_building: document.getElementById('st-dorm_building').value.trim() || null,
            dorm_room_number: document.getElementById('st-dorm_room_number').value.trim() || null,
            bed_number: document.getElementById('st-bed_number').value.trim() || null,
            remark: document.getElementById('st-remark').value.trim()
        };
        if(!sd.student_no||!sd.name||!sd.gender||!sd.grade) { alert('请填写完整信息'); return; }
        if(id) {
            fetch(`/api/admin/students/${id}`, {
                method:'PUT',
                headers:{'Content-Type':'application/json'},
                body:JSON.stringify(sd)
            }).then(r=>r.json()).then(res=>{
                if(res.success) { closeModal(); loadStudents(stPage); alert('修改成功'); }
                else alert(res.message||'修改失败');
            });
        } else {
            fetch('/api/admin/students', {
                method:'POST',
                headers:{'Content-Type':'application/json'},
                body:JSON.stringify(sd)
            }).then(r=>r.json()).then(res=>{
                if(res.success) { closeModal(); loadStudents(1); alert('添加成功'); }
                else alert(res.message||'添加失败');
            });
        }
    };
}

// ======= 宿舍奖项 =======
let awPage = 1, awTotal = 0, awPerPage = 100;
function loadAwards(page=1) {
    awPage = page;
    fetch(`/api/admin/dorm_awards?page=${page}&per_page=${awPerPage}`).then(r=>r.json()).then(res=>{
        const data = res.data || [];
        awTotal = res.total || 0;
        let tb='';
        data.forEach(a=>{
            tb+=`<tr>
                <td>${(a.building && a.room_number) ? (a.building + '-' + a.room_number) : ''}</td>
                <td>${a.award_type}</td>
                <td>${a.term}</td>
                <td>${a.reason||''}</td>
                <td>${a.award_time||''}</td>
                <td>
                    <button type="button" onclick="editAward(${a.id})">修改</button>
                    <button type="button" onclick="deleteAward(${a.id})">删除</button>
                </td>
            </tr>`;
        });
        document.getElementById('award-tbody').innerHTML = tb;
        renderAwardPagination();
    });
}
function renderAwardPagination() {
    const totalPages = Math.ceil(awTotal / awPerPage);
    let html = '';
    if (totalPages > 1) {
        html += `<button type="button" ${awPage===1?'disabled':''} onclick="loadAwards(${awPage-1})">上一页</button>`;
        let start = Math.max(1, awPage-2), end = Math.min(totalPages, awPage+2);
        if (start > 1) html += `<span>...</span>`;
        for(let i=start;i<=end;i++){
            html += `<button type="button" ${i===awPage?'style="font-weight:bold"':''} onclick="loadAwards(${i})">${i}</button>`;
        }
        if (end < totalPages) html += `<span>...</span>`;
        html += `<button type="button" ${awPage===totalPages?'disabled':''} onclick="loadAwards(${awPage+1})">下一页</button>`;
    }
    document.getElementById('award-pagination').innerHTML = html;
}
document.getElementById('add-award-btn').onclick = () => showAwardModal('add');
window.editAward = function(id) {
    fetch(`/api/admin/dorm_awards?page=${awPage}&per_page=${awPerPage}`).then(r=>r.json()).then(res=>{
        const a = (res.data||[]).find(x=>x.id==id);
        if(a) showAwardModal('edit', a);
        else alert('获取数据失败');
    });
};
window.deleteAward = function(id) {
    if(confirm('确定要删除该奖惩吗？')) {
        fetch(`/api/admin/dorm_awards/${id}`, {method:'DELETE'})
        .then(r=>r.json())
        .then(res=>{
            if(res.success) { loadAwards(awPage); alert('删除成功'); }
            else alert(res.message || '删除失败');
        });
    }
};
function showAwardModal(type, a) {
    document.getElementById('modal-bg').style.display = 'block';
    document.getElementById('modal').style.display = 'block';
    document.getElementById('modal-title').textContent = type==='add'?'新增奖惩':'修改奖惩';
    const form = document.getElementById('modal-form');
    form.innerHTML = `
        <div style="margin-bottom:13px">
            <label>宿舍楼：
                <select id="aw-building" style="width:90px">
                    <option value="">请选择</option>
                    <option value="A">A</option>
                    <option value="B">B</option>
                    <option value="C">C</option>
                    <option value="D">D</option>
                    <option value="E">E</option>
                    <option value="F">F</option>
                    <option value="G">G</option>
                    <option value="H">H</option>
                    <option value="I">I</option>
                    <option value="J">J</option>
                    <option value="K">K</option>
                    <option value="L">L</option>
                    <option value="M">M</option>
                </select>
            </label>
        </div>
        <div style="margin-bottom:13px">
            <label>房间号：<input type="text" id="aw-room_number" style="width:60px"></label>
        </div>
        <div style="margin-bottom:13px"><label>奖惩类型：<input type="text" id="aw-award_type" required style="width:200px"></label></div>
        <div style="margin-bottom:13px"><label>学期：<input type="text" id="aw-term" required style="width:200px"></label></div>
        <div style="margin-bottom:13px"><label>理由：<input type="text" id="aw-reason" style="width:200px"></label></div>
        <div style="margin-bottom:13px"><label>获该奖惩时间：<input type="date" id="aw-award_time" required style="width:200px"></label></div>
        <div style="text-align:right;margin-top:20px;">
            <button type="button" id="modal-cancel">取消</button>
            <button type="submit" id="modal-ok">确定</button>
        </div>
    `;
    if(type==='edit' && a) {
        document.getElementById('aw-building').value = a.building||'';
        document.getElementById('aw-room_number').value = a.room_number||'';
        document.getElementById('aw-award_type').value = a.award_type;
        document.getElementById('aw-term').value = a.term;
        document.getElementById('aw-reason').value = a.reason||'';
        document.getElementById('aw-award_time').value = a.award_time? a.award_time.split('T')[0]: '';
        form.dataset.editId = a.id;
    } else {
        form.dataset.editId = '';
    }
    form.onsubmit = null;
    document.getElementById('modal-cancel').onclick = closeModal;
    document.getElementById('modal-bg').onclick = closeModal;
    form.onsubmit = function(e) {
        e.preventDefault();
        const id = form.dataset.editId;
        const awd = {
            building: document.getElementById('aw-building').value,
            room_number: document.getElementById('aw-room_number').value.trim(),
            award_type: document.getElementById('aw-award_type').value.trim(),
            term: document.getElementById('aw-term').value.trim(),
            reason: document.getElementById('aw-reason').value.trim(),
            award_time: document.getElementById('aw-award_time').value
        };
        if(!awd.building || !awd.room_number || !awd.award_type || !awd.term || !awd.award_time) { alert('请填写完整信息'); return; }
        if(id) {
            fetch(`/api/admin/dorm_awards/${id}`, {
                method:'PUT',
                headers:{'Content-Type':'application/json'},
                body:JSON.stringify(awd)
            }).then(r=>r.json()).then(res=>{
                if(res.success) { closeModal(); loadAwards(awPage); alert('修改成功'); }
                else alert(res.message||'修改失败');
            });
        } else {
            fetch('/api/admin/dorm_awards', {
                method:'POST',
                headers:{'Content-Type':'application/json'},
                body:JSON.stringify(awd)
            }).then(r=>r.json()).then(res=>{
                if(res.success) { closeModal(); loadAwards(1); alert('添加成功'); }
                else alert(res.message||'添加失败');
            });
        }
    };
}

// ======= 宿舍检查 =======
let ckPage = 1, ckTotal = 0, ckPerPage = 100;
function loadChecks(page=1) {
    ckPage = page;
    fetch(`/api/admin/dorm_checks?page=${page}&per_page=${ckPerPage}`).then(r=>r.json()).then(res=>{
        const data = res.data || [];
        ckTotal = res.total || 0;
        let tb='';
        data.forEach(c=>{
            tb+=`<tr>
                <td>${(c.building && c.room_number) ? (c.building + '-' + c.room_number) : ''}</td>
                <td>${c.check_date||''}</td>
                <td>${c.checker||''}</td>
                <td>${c.score||''}</td>
                <td>${c.remarks||''}</td>
                <td>${c.rectify_text || ''}</td>
                <td>
                    <button type="button" onclick="editCheck(${c.id})">修改</button>
                    <button type="button" onclick="deleteCheck(${c.id})">删除</button>
                </td>
            </tr>`;
        });
        document.getElementById('check-tbody').innerHTML = tb;
        renderCheckPagination();
    });
}
function renderCheckPagination() {
    const totalPages = Math.ceil(ckTotal / ckPerPage);
    let html = '';
    if (totalPages > 1) {
        html += `<button type="button" ${ckPage===1?'disabled':''} onclick="loadChecks(${ckPage-1})">上一页</button>`;
        let start = Math.max(1, ckPage-2), end = Math.min(totalPages, ckPage+2);
        if (start > 1) html += `<span>...</span>`;
        for(let i=start;i<=end;i++){
            html += `<button type="button" ${i===ckPage?'style="font-weight:bold"':''} onclick="loadChecks(${i})">${i}</button>`;
        }
        if (end < totalPages) html += `<span>...</span>`;
        html += `<button type="button" ${ckPage===totalPages?'disabled':''} onclick="loadChecks(${ckPage+1})">下一页</button>`;
    }
    document.getElementById('check-pagination').innerHTML = html;
}
document.getElementById('add-check-btn').onclick = () => showCheckModal('add');
window.editCheck = function(id) {
    fetch(`/api/admin/dorm_checks?page=${ckPage}&per_page=${ckPerPage}`).then(r=>r.json()).then(res=>{
        const c = (res.data||[]).find(x=>x.id==id);
        if(c) showCheckModal('edit', c);
        else alert('获取数据失败');
    });
};
window.deleteCheck = function(id) {
    if(confirm('确定要删除该检查记录吗？')) {
        fetch(`/api/admin/dorm_checks/${id}`, {method:'DELETE'})
        .then(r=>r.json())
        .then(res=>{
            if(res.success) { loadChecks(ckPage); alert('删除成功'); }
            else alert(res.message || '删除失败');
        });
    }
};
function showCheckModal(type, c) {
    document.getElementById('modal-bg').style.display = 'block';
    document.getElementById('modal').style.display = 'block';
    document.getElementById('modal-title').textContent = type==='add'?'新增检查':'修改检查';
    const form = document.getElementById('modal-form');
    form.innerHTML = `
        <div style="margin-bottom:13px">
            <label>宿舍楼：
                <select id="ck-building" style="width:90px">
                    <option value="">请选择</option>
                    <option value="A">A</option>
                    <option value="B">B</option>
                    <option value="C">C</option>
                    <option value="D">D</option>
                    <option value="E">E</option>
                    <option value="F">F</option>
                    <option value="G">G</option>
                    <option value="H">H</option>
                    <option value="I">I</option>
                    <option value="J">J</option>
                    <option value="K">K</option>
                    <option value="L">L</option>
                    <option value="M">M</option>
                </select>
            </label>
        </div>
        <div style="margin-bottom:13px">
            <label>房间号：<input type="text" id="ck-room_number" style="width:60px"></label>
        </div>
        <div style="margin-bottom:13px"><label>检查日期：<input type="date" id="ck-check_date" required style="width:200px"></label></div>
        <div style="margin-bottom:13px"><label>检查人：<input type="text" id="ck-checker" style="width:200px"></label></div>
        <div style="margin-bottom:13px"><label>分数：<input type="number" id="ck-score" required style="width:200px" min="0" max="100"></label></div>
        <div style="margin-bottom:13px"><label>备注：<input type="text" id="ck-remarks" style="width:200px"></label></div>
        <div style="margin-bottom:13px"><label>已整改：<select id="ck-rectified"><option value="0">否</option><option value="1">是</option></select></label></div>
        <div style="text-align:right;margin-top:20px;">
            <button type="button" id="modal-cancel">取消</button>
            <button type="submit" id="modal-ok">确定</button>
        </div>
    `;
    if(type==='edit' && c) {
        document.getElementById('ck-building').value = c.building||'';
        document.getElementById('ck-room_number').value = c.room_number||'';
        document.getElementById('ck-check_date').value = c.check_date? c.check_date.split('T')[0]: '';
        document.getElementById('ck-checker').value = c.checker||'';
        document.getElementById('ck-score').value = c.score||'';
        document.getElementById('ck-remarks').value = c.remarks||'';
        document.getElementById('ck-rectified').value = c.rectified? 1 : 0;
        form.dataset.editId = c.id;
    } else {
        form.dataset.editId = '';
    }
    form.onsubmit = null;
    document.getElementById('modal-cancel').onclick = closeModal;
    document.getElementById('modal-bg').onclick = closeModal;
    form.onsubmit = function(e) {
        e.preventDefault();
        const id = form.dataset.editId;
        const ck = {
            building: document.getElementById('ck-building').value,
            room_number: document.getElementById('ck-room_number').value.trim(),
            check_date: document.getElementById('ck-check_date').value,
            checker: document.getElementById('ck-checker').value.trim(),
            score: document.getElementById('ck-score').value,
            remarks: document.getElementById('ck-remarks').value.trim(),
            rectified: document.getElementById('ck-rectified').value
        };
        if(!ck.building || !ck.room_number || !ck.check_date || !ck.score) { alert('请填写完整信息'); return; }
        if(id) {
            fetch(`/api/admin/dorm_checks/${id}`, {
                method:'PUT',
                headers:{'Content-Type':'application/json'},
                body:JSON.stringify(ck)
            }).then(r=>r.json()).then(res=>{
                if(res.success) { closeModal(); loadChecks(ckPage); alert('修改成功'); }
                else alert(res.message||'修改失败');
            });
        } else {
            fetch('/api/admin/dorm_checks', {
                method:'POST',
                headers:{'Content-Type':'application/json'},
                body:JSON.stringify(ck)
            }).then(r=>r.json()).then(res=>{
                if(res.success) { closeModal(); loadChecks(1); alert('添加成功'); }
                else alert(res.message||'添加失败');
            });
        }
    };
}

// ======= 访客 =======
let viPage = 1, viTotal = 0, viPerPage = 100;
function loadVisitors(page=1) {
    viPage = page;
    fetch(`/api/admin/visitors?page=${page}&per_page=${viPerPage}`).then(r=>r.json()).then(res=>{
        const data = res.data || [];
        viTotal = res.total || 0;
        let tb='';
        data.forEach(v=>{
            tb+=`<tr>
                <td>${v.name}</td>
                <td>${(v.building && v.room_number) ? (v.building + '-' + v.room_number) : ''}</td>
                <td>${(v.student_no || '') + (v.student_name ? ' ' + v.student_name : '')}</td>
                <td>${v.visit_time||''}</td>
                <td>${v.leave_time||''}</td>
                <td>${v.purpose||''}</td>
                <td>
                    <button type="button" onclick="editVisitor(${v.id})">修改</button>
                    <button type="button" onclick="deleteVisitor(${v.id})">删除</button>
                </td>
            </tr>`;
        });
        document.getElementById('visitor-tbody').innerHTML = tb;
        renderVisitorPagination();
    });
}
function renderVisitorPagination() {
    const totalPages = Math.ceil(viTotal / viPerPage);
    let html = '';
    if (totalPages > 1) {
        html += `<button type="button" ${viPage===1?'disabled':''} onclick="loadVisitors(${viPage-1})">上一页</button>`;
        let start = Math.max(1, viPage-2), end = Math.min(totalPages, viPage+2);
        if (start > 1) html += `<span>...</span>`;
        for(let i=start;i<=end;i++){
            html += `<button type="button" ${i===viPage?'style="font-weight:bold"':''} onclick="loadVisitors(${i})">${i}</button>`;
        }
        if (end < totalPages) html += `<span>...</span>`;
        html += `<button type="button" ${viPage===totalPages?'disabled':''} onclick="loadVisitors(${viPage+1})">下一页</button>`;
    }
    document.getElementById('visitor-pagination').innerHTML = html;
}
window.editVisitor = function(id) {
    fetch(`/api/admin/visitors?page=${viPage}&per_page=${viPerPage}`).then(r=>r.json()).then(res=>{
        const v = (res.data||[]).find(x=>x.id==id);
        if(v) showVisitorModal('edit', v);
        else alert('获取数据失败');
    });
};
window.deleteVisitor = function(id) {
    if(confirm('确定要删除该访客记录吗？')) {
        fetch(`/api/admin/visitors/${id}`, {method:'DELETE'})
        .then(r=>r.json())
        .then(res=>{
            if(res.success) { loadVisitors(viPage); alert('删除成功'); }
            else alert(res.message || '删除失败');
        });
    }
};
function showVisitorModal(type, v) {
    document.getElementById('modal-bg').style.display = 'block';
    document.getElementById('modal').style.display = 'block';
    document.getElementById('modal-title').textContent = '修改访客记录';
    const form = document.getElementById('modal-form');
    form.innerHTML = `
        <div style="margin-bottom:13px"><label>姓名：<input type="text" id="vi-name" required style="width:200px"></label></div>
        <div style="margin-bottom:13px">
            <label>宿舍楼：
                <select id="vi-building" style="width:90px">
                    <option value="">请选择</option>
                    <option value="A">A</option>
                    <option value="B">B</option>
                    <option value="C">C</option>
                    <option value="D">D</option>
                    <option value="E">E</option>
                    <option value="F">F</option>
                    <option value="G">G</option>
                    <option value="H">H</option>
                    <option value="I">I</option>
                    <option value="J">J</option>
                    <option value="K">K</option>
                    <option value="L">L</option>
                    <option value="M">M</option>
                </select>
            </label>
        </div>
        <div style="margin-bottom:13px"><label>房间号：<input type="text" id="vi-room_number" style="width:60px"></label></div>
        <div style="margin-bottom:13px"><label>被访学生学号：<input type="text" id="vi-student_no" style="width:120px"></label></div>
        <div style="margin-bottom:13px"><label>被访学生姓名：<input type="text" id="vi-student_name" style="width:120px"></label></div>
        <div style="margin-bottom:13px"><label>来访时间：<input type="datetime-local" id="vi-visit_time" required style="width:200px"></label></div>
        <div style="margin-bottom:13px"><label>离开时间：<input type="datetime-local" id="vi-leave_time" style="width:200px"></label></div>
        <div style="margin-bottom:13px"><label>来访事由：<input type="text" id="vi-purpose" style="width:200px"></label></div>
        <div style="text-align:right;margin-top:20px;">
            <button type="button" id="modal-cancel">取消</button>
            <button type="submit" id="modal-ok">确定</button>
        </div>
    `;
    document.getElementById('vi-name').value = v.name||'';
    document.getElementById('vi-building').value = v.building||'';
    document.getElementById('vi-room_number').value = v.room_number||'';
    document.getElementById('vi-student_no').value = v.student_no||'';
    document.getElementById('vi-student_name').value = v.student_name||'';
    document.getElementById('vi-visit_time').value = v.visit_time ? v.visit_time.replace(' ', 'T').slice(0,16) : '';
    document.getElementById('vi-leave_time').value = v.leave_time ? v.leave_time.replace(' ', 'T').slice(0,16) : '';
    document.getElementById('vi-purpose').value = v.purpose||'';
    form.dataset.editId = v.id;
    form.onsubmit = null;
    document.getElementById('modal-cancel').onclick = closeModal;
    document.getElementById('modal-bg').onclick = closeModal;
    form.onsubmit = function(e) {
        e.preventDefault();
        const id = form.dataset.editId;
        const vi = {
            name: document.getElementById('vi-name').value.trim(),
            building: document.getElementById('vi-building').value,
            room_number: document.getElementById('vi-room_number').value.trim(),
            student_no: document.getElementById('vi-student_no').value.trim(),
            student_name: document.getElementById('vi-student_name').value.trim(),
            visit_time: document.getElementById('vi-visit_time').value,
            leave_time: document.getElementById('vi-leave_time').value||null,
            purpose: document.getElementById('vi-purpose').value.trim()
        };
        if(!vi.name||!vi.building||!vi.room_number||!vi.visit_time) { alert('请填写完整信息'); return; }
        fetch(`/api/admin/visitors/${id}`, {
            method:'PUT',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify(vi)
        }).then(r=>r.json()).then(res=>{
            if(res.success) { closeModal(); loadVisitors(viPage); alert('修改成功'); }
            else alert(res.message||'修改失败');
        });
    };
}

// ========== 全局查询 ==========
document.getElementById('global-search-btn').onclick = function() {
    const kw = document.getElementById('global-search-input').value.trim();
    if(!kw) return;
    fetch(`/api/admin/search?q=${encodeURIComponent(kw)}`).then(r=>r.json()).then(res=>{
        if(!res.success) { alert('查询失败'); return; }
        const d = res.data;
        let html = '';
        // 学生
        html += `<h4>学生信息</h4>`;
        if(d.students && d.students.length)
            html += '<table class="search-tab"><tr><th>学号</th><th>姓名</th><th>性别</th><th>年级</th><th>电话</th><th>宿舍</th><th>床号</th><th>操作</th></tr>' +
                d.students.map(s=>`<tr>
                    <td>${s.student_no}</td>
                    <td>${s.name}</td>
                    <td>${s.gender==='M'?'男':'女'}</td>
                    <td>${s.grade||''}</td>
                    <td>${s.phone||''}</td>
                    <td>${(s.dorm_building && s.dorm_room_number)?(s.dorm_building+'-'+s.dorm_room_number):''}</td>
                    <td>${s.bed_number||''}</td>
                    <td>
                        <button onclick="editStudent(${s.id})">修改</button>
                        <button onclick="deleteStudent(${s.id})">删除</button>
                    </td>
                </tr>`).join('') + '</table>';
        else html += '<div style="color:#888;">无</div>';
        // 奖项
        html += `<h4 style="margin-top:18px;">宿舍奖项</h4>`;
        if(d.awards && d.awards.length)
            html += '<table class="search-tab"><tr><th>宿舍</th><th>奖项类型</th><th>学期</th><th>理由</th><th>获奖时间</th><th>操作</th></tr>' +
                d.awards.map(a=>`<tr>
                    <td>${(a.building && a.room_number)?(a.building+'-'+a.room_number):''}</td>
                    <td>${a.award_type}</td>
                    <td>${a.term}</td>
                    <td>${a.reason||''}</td>
                    <td>${a.award_time||''}</td>
                    <td>
                        <button onclick="editAward(${a.id})">修改</button>
                        <button onclick="deleteAward(${a.id})">删除</button>
                    </td>
                </tr>`).join('') + '</table>';
        else html += '<div style="color:#888;">无</div>';
        // 检查
        html += `<h4 style="margin-top:18px;">宿舍检查</h4>`;
        if(d.checks && d.checks.length)
            html += '<table class="search-tab"><tr><th>宿舍</th><th>日期</th><th>检查人</th><th>分数</th><th>备注</th><th>整改</th><th>操作</th></tr>' +
                d.checks.map(c=>`<tr>
                    <td>${(c.building && c.room_number)?(c.building+'-'+c.room_number):''}</td>
                    <td>${c.check_date||''}</td>
                    <td>${c.checker||''}</td>
                    <td>${c.score||''}</td>
                    <td>${c.remarks||''}</td>
                    <td>${c.score>85?'无需整改':(c.rectified?'已整改':'未整改')}</td>
                    <td>
                        <button onclick="editCheck(${c.id})">修改</button>
                        <button onclick="deleteCheck(${c.id})">删除</button>
                    </td>
                </tr>`).join('') + '</table>';
        else html += '<div style="color:#888;">无</div>';
        // 访客
        html += `<h4 style="margin-top:18px;">访客记录</h4>`;
        if(d.visitors && d.visitors.length)
            html += '<table class="search-tab"><tr><th>姓名</th><th>宿舍</th><th>被访学生</th><th>来访</th><th>离开</th><th>事由</th><th>操作</th></tr>' +
                d.visitors.map(v=>`<tr>
                    <td>${v.name}</td>
                    <td>${(v.building && v.room_number)?(v.building+'-'+v.room_number):''}</td>
                    <td>${(v.student_no||'')+(v.student_name?' '+v.student_name:'')}</td>
                    <td>${v.visit_time||''}</td>
                    <td>${v.leave_time||''}</td>
                    <td>${v.purpose||''}</td>
                    <td>
                        <button onclick="editVisitor(${v.id})">修改</button>
                        <button onclick="deleteVisitor(${v.id})">删除</button>
                    </td>
                </tr>`).join('') + '</table>';
        else html += '<div style="color:#888;">无</div>';
        document.getElementById('global-search-result').innerHTML = html;
        document.getElementById('global-search-modal').style.display = 'block';
    });
};
document.getElementById('global-search-input').onkeydown = function(e){
    if(e.keyCode===13) document.getElementById('global-search-btn').onclick();
};
window.closeGlobalSearchModal = function(){
    document.getElementById('global-search-modal').style.display = 'none';
};

// 公用关闭弹窗
function closeModal() {
    document.getElementById('modal-bg').style.display = 'none';
    document.getElementById('modal').style.display = 'none';
}

// 管理员信息显示
function showCurrentAdminInfo() {
    fetch('/api/admin/current_admin').then(r=>r.json()).then(res=>{
        let txt = '';
        if(res.success) {
            txt = `管理员${res.data.name}，你好，您管理的楼栋是：${res.data.building}`;
        }
        document.getElementById('current-admin-bar-top').textContent = txt;
    });
}

// ======= 退出登录按钮事件 =======
document.addEventListener('DOMContentLoaded', function() {
    let logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.onclick = async function() {
            await fetch('/api/admin/logout', {method: 'POST'});
            window.location.href = '/login.html';
        };
    }
});

// ======= 统计分析 =======
window.occupancyChart = null;
window.awardChart = null;
window.visitorChart = null;

function loadStatsCharts(mode="occupancy") {
    if(mode === "occupancy") {
        let dom = document.getElementById('chart-occupancy');
        if (window.occupancyChart) {
            window.occupancyChart.dispose();
        }
        window.occupancyChart = echarts.init(dom);
        fetch('/api/admin/stats/occupancy').then(r=>r.json()).then(res=>{
            if(!res.success) return;
            window.occupancyChart.setOption({
                title:{text:'宿舍楼入住率', left:'center'},
                tooltip:{},
                xAxis:{data:res.data.map(d=>d.building), name:"楼栋"},
                yAxis:{max:1, axisLabel:{formatter: v=>(v*100).toFixed(0)+"%"}},
                series:[{
                    type:'bar',
                    name:'入住率',
                    data:res.data.map(d=>d.rate),
                    label:{show:true, formatter: p=>(p.value*100).toFixed(1)+'%'}
                }]
            });
            setTimeout(()=>{window.occupancyChart.resize();}, 10);
        });
        setStatsNavActive('occupancy');
    } else if(mode === "award") {
        let dom = document.getElementById('chart-award');
        if (window.awardChart) window.awardChart.dispose();
        window.awardChart = echarts.init(dom);
        fetch('/api/admin/stats/award_ratio').then(r=>r.json()).then(res=>{
            if(!res.success) return;
            window.awardChart.setOption({
                title:{text:'奖惩比例', left:'center'},
                tooltip:{},
                series:[{
                    type:'pie',
                    radius: ['40%', '70%'],
                    data:[
                        {value:res.data.award, name:'奖'},
                        {value:res.data.punish, name:'惩'}
                    ],
                    label:{formatter:'{b}: {d}%'}
                }]
            });
            setTimeout(()=>{window.awardChart.resize();}, 10);
        });
        setStatsNavActive('award');
    } else if(mode === "visitor") {
        let dom = document.getElementById('chart-visitor');
        if (window.visitorChart) window.visitorChart.dispose();
        window.visitorChart = echarts.init(dom);
        fetch('/api/admin/stats/visitor_types').then(r=>r.json()).then(res=>{
            if(!res.success) return;
            // 只显示前30个类型，其余合并为“其他”
            let arr = res.data.sort((a,b)=>b.count-a.count);
            let topN = arr.slice(0, 30);
            let othersN = arr.slice(30);
            if (othersN.length) {
                let sum = othersN.reduce((t, x)=>t+x.count, 0);
                topN.push({type: "其他", count: sum});
            }
            let pieData = topN.map(item=>({value:item.count, name:item.type||'其他'}));
            window.visitorChart.setOption({
                title:{text:'访客类型占比', left:'center'},
                tooltip:{},
                legend: {
                    type: 'scroll',
                    orient: 'vertical',
                    right: 10,
                    top: 60,
                    bottom: 20
                },
                series:[{
                    type:'pie',
                    radius: ['40%', '65%'],
                    center: ['32%', '50%'], // 靠左，右侧给legend腾空间
                    data: pieData,
                    label:{
                        formatter:'{b}: {d}%',
                        overflow: 'truncate',
                        minMargin: 2,
                        fontSize: 13
                    },
                    emphasis: {
                        label: {
                            show: true,
                            fontSize: 14,
                            fontWeight: 'bold'
                        }
                    }
                }]
            });
            setTimeout(()=>{window.visitorChart.resize();}, 10);
        });
        setStatsNavActive('visitor');
    }
}
document.getElementById("btn-stats-occupancy").onclick = function() {
    loadStatsCharts("occupancy");
    setTimeout(()=>{if(window.occupancyChart) window.occupancyChart.resize();}, 10);
};
document.getElementById("btn-stats-award").onclick = function() {
    loadStatsCharts("award");
    setTimeout(()=>{if(window.awardChart) window.awardChart.resize();}, 10);
};
document.getElementById("btn-stats-visitor").onclick = function() {
    loadStatsCharts("visitor");
    setTimeout(()=>{if(window.visitorChart) window.visitorChart.resize();}, 10);
};
function setStatsNavActive(mode) {
    document.getElementById("btn-stats-occupancy").classList.toggle("active", mode === "occupancy");
    document.getElementById("btn-stats-award").classList.toggle("active", mode === "award");
    document.getElementById("btn-stats-visitor").classList.toggle("active", mode === "visitor");
    document.getElementById("chart-occupancy").style.display = mode === "occupancy" ? "block" : "none";
    document.getElementById("chart-award").style.display = mode === "award" ? "block" : "none";
    document.getElementById("chart-visitor").style.display = mode === "visitor" ? "block" : "none";
}

let bedPage = 1, bedTotal = 0, bedPerPage = 100;

function loadBedList(page=1) {
    bedPage = page;
    fetch(`/api/admin/beds?page=${page}&per_page=${bedPerPage}`)
        .then(r=>r.json()).then(res=>{
            const data = res.data || [];
            bedTotal = res.total || 0;
            let tb = '';
            data.forEach(b=>{
                tb += `<tr>
                    <td>${b.dorm_building}</td>
                    <td>${b.dorm_room_number}</td>
                    <td>${b.bed_number}</td>
                    <td>${b.status}</td>
                    <td>${b.student_no||''}</td>
                    <td>${b.student_name||''}</td>
                </tr>`;
            });
            document.getElementById('bed-tbody').innerHTML = tb;
            renderBedPagination();
        });
}

function renderBedPagination() {
    const totalPages = Math.ceil(bedTotal / bedPerPage);
    let html = '';
    if (totalPages > 1) {
        html += `<button type="button" ${bedPage===1?'disabled':''} onclick="loadBedList(${bedPage-1})">上一页</button>`;
        let start = Math.max(1, bedPage-2), end = Math.min(totalPages, bedPage+2);
        if (start > 1) html += `<span>...</span>`;
        for(let i=start;i<=end;i++){
            html += `<button type="button" ${i===bedPage?'style="font-weight:bold"':''} onclick="loadBedList(${i})">${i}</button>`;
        }
        if (end < totalPages) html += `<span>...</span>`;
        html += `<button type="button" ${bedPage===totalPages?'disabled':''} onclick="loadBedList(${bedPage+1})">下一页</button>`;
    }
    document.getElementById('bed-pagination').innerHTML = html;
}

// 获取床位筛选参数
function getBedFilters() {
    return {
        dorm_building: document.getElementById('filter-bed-building').value.trim(),
        dorm_room_number: document.getElementById('filter-bed-room').value.trim(),
        bed_number: document.getElementById('filter-bed-number').value.trim(),
        status: document.getElementById('filter-bed-status').value,
        student_no: document.getElementById('filter-bed-student-no').value.trim(),
        student_name: document.getElementById('filter-bed-student-name').value.trim()
    };
}

function loadBedList(page=1) {
    bedPage = page;
    let url = `/api/admin/beds?page=${page}&per_page=${bedPerPage}`;
    // 拼接筛选参数
    const filters = getBedFilters();
    Object.keys(filters).forEach(k => {
        if (filters[k]) url += `&${k}=${encodeURIComponent(filters[k])}`;
    });
    fetch(url)
        .then(r=>r.json()).then(res=>{
            const data = res.data || [];
            bedTotal = res.total || 0;
            let tb = '';
            data.forEach(b=>{
                tb += `<tr>
                    <td>${b.dorm_building}</td>
                    <td>${b.dorm_room_number}</td>
                    <td>${b.bed_number}</td>
                    <td>${b.status}</td>
                    <td>${b.student_no||''}</td>
                    <td>${b.student_name||''}</td>
                </tr>`;
            });
            document.getElementById('bed-tbody').innerHTML = tb;
            renderBedPagination();
        });
}

// 筛选栏按钮绑定
document.getElementById('filter-bed-btn').onclick = function() {
    loadBedList(1);
};
document.getElementById('reset-bed-filter-btn').onclick = function() {
    document.getElementById('filter-bed-building').value = '';
    document.getElementById('filter-bed-room').value = '';
    document.getElementById('filter-bed-number').value = '';
    document.getElementById('filter-bed-status').value = '';
    document.getElementById('filter-bed-student-no').value = '';
    document.getElementById('filter-bed-student-name').value = '';
    loadBedList(1);
};

// 毕业处理弹窗显示/隐藏
document.getElementById('graduate-btn').onclick = function() {
    document.getElementById('graduate-year').value = '';
    document.getElementById('graduate-msg').textContent = '';
    document.getElementById('graduate-modal-bg').style.display = 'block';
    document.getElementById('graduate-modal').style.display = 'block';
};
document.getElementById('graduate-modal-bg').onclick =
document.getElementById('graduate-cancel-btn').onclick = function() {
    document.getElementById('graduate-modal-bg').style.display = 'none';
    document.getElementById('graduate-modal').style.display = 'none';
};
// 毕业处理提交
document.getElementById('graduate-form').onsubmit = function(e) {
    e.preventDefault();
    var year = document.getElementById('graduate-year').value.trim();
    var msg = document.getElementById('graduate-msg');
    if (!year) {
        msg.textContent = "请输入年级";
        return;
    }
    msg.textContent = "正在处理...";
    fetch(`/api/admin/students/graduate/${year}`, {
        method: 'POST'
    }).then(r=>r.json()).then(res=>{
        if (res.success) {
            msg.style.color = "#27ae60";
            msg.textContent = res.message || "毕业处理成功";
            // 自动关闭弹窗并刷新学生列表
            setTimeout(function() {
                document.getElementById('graduate-modal-bg').style.display = 'none';
                document.getElementById('graduate-modal').style.display = 'none';
                msg.style.color = "#e74c3c";
                loadStudents(1); // 你的学生列表刷新方法
            }, 1000);
        } else {
            msg.style.color = "#e74c3c";
            msg.textContent = res.message || "毕业处理失败";
        }
    }).catch(err=>{
        msg.textContent = "请求出错";
    });
};

document.getElementById('export-student-csv-btn').onclick = function() {
    // 拼接当前筛选参数
    let params = [];
    let filterFields = [
        ['graduated', document.getElementById('filter-graduated') ? document.getElementById('filter-graduated').value : ''],
        ['student_no', document.getElementById('filter-student-no').value],
        ['name', document.getElementById('filter-name').value],
        ['gender', document.getElementById('filter-gender').value],
        ['grade', document.getElementById('filter-grade').value],
        ['phone', document.getElementById('filter-phone').value],
        ['dorm_building', document.getElementById('filter-dorm-building').value],
        ['dorm_room_number', document.getElementById('filter-dorm-room').value],
        ['bed_number', document.getElementById('filter-bed-number').value]
    ];
    filterFields.forEach(([key, val])=>{
        if(val && val!=='') params.push(`${key}=${encodeURIComponent(val)}`);
    });
    let url = '/api/admin/students/export';
    if(params.length) url += '?' + params.join('&');
    // 直接下载
    window.open(url, '_blank');
};

document.getElementById('pw-modal-form').onsubmit = function(e) {
    e.preventDefault();
    var old_pw = document.getElementById('old-pw').value.trim();
    var new_pw = document.getElementById('new-pw').value.trim();
    var new_pw2 = document.getElementById('new-pw2').value.trim();
    var msg = document.getElementById('pw-msg');
    if(!old_pw || !new_pw || !new_pw2) {
        msg.textContent = "请填写完整信息";
        return;
    }
    if(new_pw !== new_pw2) {
        msg.textContent = "两次新密码不一致";
        return;
    }
    msg.textContent = "正在提交...";
    fetch('/api/admin/change_password', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ old_password: old_pw, new_password: new_pw })
    }).then(r=>r.json()).then(res=>{
        if(res.success) {
            msg.style.color = "#27ae60";
            msg.textContent = "修改成功，请重新登录";
            setTimeout(function(){
                document.getElementById('pw-modal-bg').style.display = 'none';
                document.getElementById('pw-modal').style.display = 'none';
                msg.style.color = "#e74c3c";
            }, 1200);
        } else {
            msg.textContent = res.message || "修改失败";
        }
    }).catch(()=>{msg.textContent="请求错误";});
};

document.getElementById('pw-modal-form-stu').onsubmit = function(e) {
    e.preventDefault();
    var stu_no = document.getElementById('stu-no').value.trim();
    var stu_name = document.getElementById('stu-name').value.trim();
    var stu_new_pw = document.getElementById('stu-new-pw').value.trim();
    var msg = document.getElementById('pw-stu-msg');
    if(!stu_new_pw || (!stu_no && !stu_name)) {
        msg.textContent = "请填写学生学号或姓名和新密码";
        return;
    }
    msg.textContent = "正在提交...";
    fetch('/api/admin/reset_student_password', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ student_no: stu_no, student_name: stu_name, new_password: stu_new_pw })
    }).then(r=>r.json()).then(res=>{
        if(res.success) {
            msg.style.color = "#27ae60";
            msg.textContent = res.message || "密码重置成功";
            setTimeout(function(){
                document.getElementById('pw-modal-bg-stu').style.display = 'none';
                document.getElementById('pw-modal-stu').style.display = 'none';
                msg.style.color = "#e74c3c";
            }, 1200);
        } else if(res.multi) {
            msg.textContent = "查到多个学生，请精确输入学号";
        } else {
            msg.textContent = res.message || "重置失败";
        }
    }).catch(()=>{msg.textContent="请求错误";});
};
// ======= 统计分析区顶部统计卡片（仅统计未毕业学生）=======

// --- 1. 未毕业学生总数
function loadStudentCountStat() {
    fetch('/api/admin/stats/student_count?graduated=0')
        .then(r => r.json())
        .then(res => {
            document.getElementById('student-count-value').textContent =
                res.success ? res.data.student_count : '--';
        });
}

// --- 2. 各年级未毕业人数
function loadGradeStat() {
    fetch('/api/admin/stats/student_per_grade?graduated=0')
        .then(r => r.json())
        .then(res => {
            const dom = document.getElementById('grade-count-values');
            if (!res.success || !res.data.length) {
                dom.textContent = '--';
                return;
            }
            dom.innerHTML = res.data.map(
                x => `<span style="color:#2b80ff;margin-right:12px;">${x.grade}级: <b>${x.student_count}</b></span>`
            ).join('');
        });
}

// ======= 各宿舍奖项统计功能 =======
let dormAwardData = [];
let dormAwardPage = 1;
let dormAwardTotal = 0;
const dormAwardPerPage = 100;

function loadAwardStatTable() {
    // 显示加载状态
    document.getElementById('award-table-body').innerHTML = `
        <tr>
            <td colspan="3" style="text-align: center; padding: 24px; color: #888;">
                <div>加载宿舍奖项数据中...</div>
            </td>
        </tr>
    `;

    // 获取数据
    fetch('/api/admin/stats/dorm_award_counts')
        .then(r => r.json())
        .then(res => {
            if (res.success) {
                dormAwardData = res.data || [];
                renderDormAwardTable();
            } else {
                showAwardError('加载奖项统计失败: ' + (res.message || '未知错误'));
            }
        })
        .catch(err => {
            console.error('加载奖项统计失败:', err);
            showAwardError('加载失败，请检查网络连接');
        });
}

// 渲染奖项表格
function renderDormAwardTable() {
    // 获取筛选参数
    const building = document.getElementById('award-filter-building').value.trim().toLowerCase();
    const room = document.getElementById('award-filter-room').value.trim().toLowerCase();

    // 应用筛选
    let filteredData = dormAwardData;

    if (building) {
        filteredData = filteredData.filter(item =>
            item.building && item.building.toLowerCase().includes(building)
        );
    }

    if (room) {
        filteredData = filteredData.filter(item =>
            item.room_number && item.room_number.toLowerCase().includes(room)
        );
    }

    dormAwardTotal = filteredData.length;

    // 计算统计摘要
    const totalDorms = dormAwardTotal;
    const awardedDorms = filteredData.filter(item => item.award_count > 0).length;
    const totalAwards = filteredData.reduce((sum, item) => sum + (item.award_count || 0), 0);

    // 更新摘要
    document.getElementById('award-stats-summary').innerHTML =
        `<b>统计摘要：</b>共 <span style="color:#3865d1;">${totalDorms}</span> 间宿舍,
        其中 <span style="color:#3865d1;">${awardedDorms}</span> 间获得过奖惩,
        总计 <span style="color:#3865d1;">${totalAwards}</span> 个奖惩`;

    // 计算分页
    const totalPages = Math.ceil(filteredData.length / dormAwardPerPage);
    const startIndex = (dormAwardPage - 1) * dormAwardPerPage;
    const pageData = filteredData.slice(startIndex, startIndex + dormAwardPerPage);

    const tbody = document.getElementById('award-table-body');

    // 渲染表格
    if (!pageData.length) {
        tbody.innerHTML = `
            <tr>
                <td colspan="3" style="text-align: center; padding: 24px; color: #888;">
                    <div>暂无数据</div>
                </td>
            </tr>
        `;
    } else {
        let html = '';
        pageData.forEach(item => {
            html += `
                <tr style="border-bottom: 1px solid #f0f0f0;">
                    <td style="padding: 12px 15px;">${item.building || '--'}</td>
                    <td style="padding: 12px 15px;">${item.room_number || '--'}</td>
                    <td style="padding: 12px 15px; text-align: right;">
                        <span style="display:inline-block; min-width:40px; font-weight:bold;">
                            ${item.award_count || 0}
                        </span>
                    </td>
                </tr>
            `;
        });
        tbody.innerHTML = html;
    }

    // 渲染分页
    renderAwardStatPagination(totalPages);
}

// 渲染分页控件
function renderAwardStatPagination(totalPages) {
    const paginationEl = document.getElementById('award-stat-pagination');
    if (!paginationEl) return;

    let html = '';
    if (totalPages > 1) {
        html += `<button ${dormAwardPage === 1 ? 'disabled' : ''} onclick="changeAwardPage(${dormAwardPage - 1})">上一页</button>`;

        // 显示页码范围
        let startPage = Math.max(1, dormAwardPage - 2);
        let endPage = Math.min(totalPages, dormAwardPage + 2);

        if (startPage > 1) {
            html += `<button onclick="changeAwardPage(1)">1</button>`;
            if (startPage > 2) html += `<span>...</span>`;
        }

        for (let i = startPage; i <= endPage; i++) {
            html += `<button ${i === dormAwardPage ? 'class="active"' : ''} onclick="changeAwardPage(${i})">${i}</button>`;
        }

        if (endPage < totalPages) {
            if (endPage < totalPages - 1) html += `<span>...</span>`;
            html += `<button onclick="changeAwardPage(${totalPages})">${totalPages}</button>`;
        }

        html += `<button ${dormAwardPage === totalPages ? 'disabled' : ''} onclick="changeAwardPage(${dormAwardPage + 1})">下一页</button>`;
    }

    paginationEl.innerHTML = html;
}

// 换页函数
function changeAwardPage(page) {
    if (page < 1 || page > Math.ceil(dormAwardData.length / dormAwardPerPage)) return;
    dormAwardPage = page;
    renderDormAwardTable();
}

// 筛选奖项数据
function filterAwardData() {
    dormAwardPage = 1; // 重置到第一页
    renderDormAwardTable();
}

// 重置筛选
function resetAwardFilter() {
    document.getElementById('award-filter-building').value = '';
    document.getElementById('award-filter-room').value = '';
    dormAwardPage = 1;
    renderDormAwardTable();
}

// 导出CSV
function exportAwardsToCSV() {
    if (!dormAwardData.length) {
        alert('没有数据可导出');
        return;
    }

    const header = ['宿舍楼', '房间号', '获奖次数'].join(',');
    const rows = dormAwardData.map(item =>
        [item.building || '', item.room_number || '', item.award_count || 0].join(',')
    );

    const csvContent = 'data:text/csv;charset=utf-8,\uFEFF' +
        [header].concat(rows).join('\n');

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', '宿舍奖项统计.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// 显示错误消息
function showAwardError(message) {
    const tbody = document.getElementById('award-table-body');
    if (!tbody) return;

    tbody.innerHTML = `
        <tr>
            <td colspan="3" style="text-align: center; padding: 24px; color: #e74c3c;">
                <div>${message}</div>
                <button style="margin-top:10px; padding:6px 12px; background:#3865d1; color:white; border:none; border-radius:4px; cursor:pointer;"
                        onclick="loadAwardStatTable()">重新加载</button>
            </td>
        </tr>
    `;
}

// ======= 绑定tab按钮和筛选按钮 =======
document.addEventListener('DOMContentLoaded', function() {
    // 顶部统计卡片加载
    if (document.getElementById('section-stats')) {
        loadStudentCountStat();
        loadGradeStat();
        // 默认激活的选项卡
        document.getElementById('btn-stats-occupancy').classList.add('active');
    }

    // 绑定选项卡按钮
    document.getElementById('btn-stats-occupancy').addEventListener('click', function() {
        showStatsTab('occupancy');
    });

    document.getElementById('btn-stats-award').addEventListener('click', function() {
        showStatsTab('award');
    });

    document.getElementById('btn-stats-visitor').addEventListener('click', function() {
        showStatsTab('visitor');
    });

    document.getElementById('btn-stats-dorm-award').addEventListener('click', function() {
        showStatsTab('dorm-award');
    });

    // 绑定筛选按钮
    document.getElementById('award-filter-btn').addEventListener('click', filterAwardData);
    document.getElementById('award-filter-reset-btn').addEventListener('click', resetAwardFilter);

    // 绑定导出按钮
    document.getElementById('export-awards-btn').addEventListener('click', exportAwardsToCSV);
});

// 切换选项卡显示
function showStatsTab(tab) {
    // 更新按钮状态
    ['occupancy', 'award', 'visitor', 'dorm-award'].forEach(k => {
        const btn = document.getElementById(`btn-stats-${k}`);
        if (btn) btn.classList.toggle('active', tab === k);
    });

    // 显示/隐藏区域
    document.getElementById('chart-occupancy').style.display = tab === 'occupancy' ? 'block' : 'none';
    document.getElementById('chart-award').style.display = tab === 'award' ? 'block' : 'none';
    document.getElementById('chart-visitor').style.display = tab === 'visitor' ? 'block' : 'none';
    document.getElementById('dorm-award-table-section').style.display = tab === 'dorm-award' ? 'block' : 'none';

    // 加载对应内容
    if (tab === 'dorm-award') {
        if (dormAwardData.length > 0) {
            renderDormAwardTable();
        } else {
            loadAwardStatTable();
        }
    }
    // 以下是占位函数，实际开发中需要实现
    else if (tab === 'occupancy') {
        // 加载入住率图表
        console.log("加载入住率图表");
    }
    else if (tab === 'award') {
        // 加载奖惩比例图表
        console.log("加载奖惩比例图表");
    }
    else if (tab === 'visitor') {
        // 加载访客类型占比图表
        console.log("加载访客类型占比图表");
    }
}

showCurrentAdminInfo();
// 默认加载学生
loadStudents();