#!/usr/bin/env python3
"""AI味检测与标记脚本 - 扫描文本中的AI高频词和模式，输出问题标记和修改建议"""

import re
import json
import sys
from pathlib import Path

# 一级禁词：出现即标记为严重
LEVEL1_BANNED = [
    "不禁", "宛如", "犹如", "仿佛", "恍若", "宛若", "恍如", "恰似"
]

# 二级禁词：严格控制
LEVEL2_BANNED = [
    "不由得", "默默地", "缓缓地", "渐渐地", "淡淡地", "深深地", "轻轻地",
    "凝视", "注视", "仰望", "眺望", "环顾", "凝望", "驻足"
]

# 三级警惕词
LEVEL3_WATCH = [
    "此刻", "内心深处", "一种.*?的感觉", "不由自主", "油然而生",
    "莫名其妙", "若有所思", "心头一紧", "心头一颤", "心头一暖",
    "嘴角上扬", "空气中弥漫着", "时间仿佛静止",
    # 新增的AI偏爱词
    "指尖", "闷闷的", "闷声", "薄薄", "堆满", "堆着", "堆砌", "周到"
]

# 句式模式
SENTENCE_PATTERNS = [
    (r"在.{2,8}之中", "「在...之中」句式套路"),
    (r"随着.{2,8}[，,]", "「随着...」万能开头"),
    (r"他.{0,3}不禁.{1,10}，.{2,15}想", "「不禁+动作+想法」AI模板"),
    (r"在.{2,6}(月光|阳光|灯光|暮色)下", "「在XX光下」套路描写"),
    (r"此时此刻", "「此时此刻」空洞强调"),
    (r"一阵.{2,4}涌上心头", "「一阵XX涌上心头」空洞感受"),
    (r"([^。！？]{5,20})[，,]([^。！？]{5,20})[，,]([^。！？]{5,20})", "三连排比句式"),
]

# 替代建议
REPLACEMENTS = {
    "不禁": "直接写动作",
    "宛如": "像、跟……似的",
    "犹如": "像、好比",
    "仿佛": "用比喻替代，或直接描写",
    "恍若": "像、似乎",
    "宛若": "像",
    "恍如": "像",
    "恰似": "像",
    "不由得": "直接写动作/反应",
    "默默地": "低头、背过身、攥紧拳头",
    "缓缓地": "找更具体的速度描述，或直接删",
    "渐渐地": "用变化本身替代：天暗了、声音远了",
    "淡淡地": "用神态细节替代：嘴角一勾、眼皮都没抬",
    "深深地": "直接写感受或动作",
    "轻轻地": "指尖碰了一下、几乎听不见地",
    "凝视": "盯着看、目光落在……上",
    "注视": "看着、盯着",
    "仰望": "抬头看",
    "眺望": "看向远处",
    "环顾": "扫了一眼",
    "凝望": "看着",
    "驻足": "停下、站住了",
    # 三级词（措辞与 banned_words.md 一致）
    "指尖": "手指、指节、手",
    "闷闷的": "直接写声音状态：压低声音、含糊地应了一声",
    "闷声": "直接写声音状态：压低声音、含糊地应了一声",
    "薄薄": "写具体：光、雾、汗，不要用'薄'敷衍",
    "堆满": "散落、摞着、漫出来、排满",
    "堆着": "散落、摞着、漫出来、排满",
    "堆砌": "散落、摞着、漫出来、排满",
    "周到": "删掉形容词，直接写他具体做了什么（如：提前调好了空调）",
    # 三级其余词（措辞与 banned_words.md 一致；三级检测仍用硬编码建议，此表仅为覆盖完整）
    "在……之中": "改为直接陈述",
    "随着……": "换起句方式",
    "此刻": "直接切入场景",
    "内心深处": "用行为暗示内心",
    "一种……的感觉": "具体化这个感觉",
    "不由自主": "写具体反应",
    "油然而生": "日常化表达",
    "莫名其妙": "说出具体哪里奇怪",
    "若有所思": "写出思考的具体内容或表情",
    "心头一紧/一颤/一暖": "换更独特的身体反应",
    "嘴角上扬": "写更自然的笑法",
    "空气中弥漫着": "具体写出什么味道",
    "时间仿佛静止": "换表达",
}

def detect_ai_flavor(text: str) -> dict:
    """检测文本中的AI味问题，返回问题列表和统计"""
    issues = []
    
    # 按行检测
    lines = text.split('\n')
    for line_num, line in enumerate(lines, 1):
        if not line.strip():
            continue
            
        # 一级禁词检测
        for word in LEVEL1_BANNED:
            if word in line:
                issues.append({
                    "severity": "严重",
                    "line": line_num,
                    "type": "禁词",
                    "found": word,
                    "context": line.strip()[:80],
                    "suggestion": REPLACEMENTS.get(word, "替换或删除")
                })
        
        # 二级禁词检测
        for word in LEVEL2_BANNED:
            if word in line:
                issues.append({
                    "severity": "警告",
                    "line": line_num,
                    "type": "高频词",
                    "found": word,
                    "context": line.strip()[:80],
                    "suggestion": REPLACEMENTS.get(word, "替换或删除")
                })
        
        # 三级警惕词检测
        for pattern in LEVEL3_WATCH:
            match = re.search(pattern, line)
            if match:
                issues.append({
                    "severity": "提醒",
                    "line": line_num,
                    "type": "警惕词",
                    "found": match.group(),
                    "context": line.strip()[:80],
                    "suggestion": "注意使用频率，考虑替代表达"
                })
        
        # 句式模式检测
        for pattern, desc in SENTENCE_PATTERNS:
            match = re.search(pattern, line)
            if match:
                issues.append({
                    "severity": "警告",
                    "line": line_num,
                    "type": "句式模式",
                    "found": match.group()[:30],
                    "context": line.strip()[:80],
                    "suggestion": desc
                })
    
    # 统计
    severity_count = {"严重": 0, "警告": 0, "提醒": 0}
    for issue in issues:
        severity_count[issue["severity"]] += 1
    
    # 段落节奏检测：连续短句或连续长句
    paragraph_rhythm = detect_rhythm(text)
    
    # AIGC检测8维度分析
    aigc_analysis = detect_aigc_dimensions(text)
    
    return {
        "total_issues": len(issues),
        "severity_count": severity_count,
        "issues": issues,
        "rhythm": paragraph_rhythm,
        "aigc_dimensions": aigc_analysis
    }


def detect_rhythm(text: str) -> list:
    """检测段落节奏问题：连续相似长度句子"""
    problems = []
    lines = text.split('\n')
    
    for line_num, line in enumerate(lines, 1):
        if not line.strip():
            continue
        # 简单按句号分句
        sentences = [s.strip() for s in re.split(r'[。！？]', line) if s.strip()]
        if len(sentences) >= 3:
            lengths = [len(s) for s in sentences[:5]]
            # 检查连续3句长度相近（差值<5字符）
            for i in range(len(lengths) - 2):
                if abs(lengths[i] - lengths[i+1]) < 5 and abs(lengths[i+1] - lengths[i+2]) < 5:
                    problems.append({
                        "line": line_num,
                        "type": "节奏单调",
                        "description": f"连续{3}句长度相近（{lengths[i]}、{lengths[i+1]}、{lengths[i+2]}字），需打破节奏"
                    })
                    break
    
    return problems


def detect_aigc_dimensions(text: str) -> dict:
    """AIGC检测8维度分析，模拟平台检测逻辑"""
    import math
    
    # 清洗文本
    clean_text = re.sub(r'[^一-鿿0-9a-zA-Z。，！？、；：""''…— \t\n]', '', text)
    chars = re.sub(r'[^\u4e00-\u9fff0-9a-zA-Z]', '', clean_text)
    if len(chars) < 100:
        return {"warning": "文本过短，AIGC维度分析不可靠"}
    
    results = {}
    alerts = []
    
    # 维度1：词汇多样性（TTR）
    # 简易分词：按2字切分
    words_2g = [chars[i:i+2] for i in range(len(chars)-1)]
    ttr = len(set(words_2g)) / len(words_2g) if words_2g else 0
    results["词汇多样性_TTR"] = round(ttr, 3)
    if ttr < 0.30:
        alerts.append("词汇多样性过低（TTR={:.3f}），AI特征明显，需增加同义替换".format(ttr))
    elif ttr < 0.50:
        alerts.append("词汇多样性偏低（TTR={:.3f}），建议增加表达变化".format(ttr))
    
    # 维度2：句长波动
    sentences = re.split(r'[。！？…]+', clean_text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 2]
    if len(sentences) >= 5:
        sent_lengths = [len(s) for s in sentences]
        avg_len = sum(sent_lengths) / len(sent_lengths)
        variance = sum((l - avg_len) ** 2 for l in sent_lengths) / len(sent_lengths)
        std_dev = math.sqrt(variance)
        results["句长标准差"] = round(std_dev, 2)
        if std_dev < 3.0:
            alerts.append("句长波动过小（std={:.2f}），句式过于均匀，需增加长短句交替".format(std_dev))
        elif std_dev > 12:
            alerts.append("句长波动过大（std={:.2f}），可能存在结构异常".format(std_dev))
    
    # 维度3：3-gram重复
    all_3grams = [chars[i:i+3] for i in range(len(chars)-2)]
    if all_3grams:
        from collections import Counter
        counter = Counter(all_3grams)
        repeated = sum(1 for c in counter.values() if c >= 3)
        repeat_ratio = repeated / len(counter) if counter else 0
        results["3gram高重复比例"] = round(repeat_ratio, 4)
        top_repeats = counter.most_common(5)
        results["3gram重复TOP5"] = [(gram, count) for gram, count in top_repeats if count >= 3]
        if repeat_ratio > 0.05:
            alerts.append("3-gram重复比例过高（{:.2%}），AI特征明显".format(repeat_ratio))
    
    # 维度4：模板化表达
    cliches = LEVEL1_BANNED + LEVEL2_BANNED
    cliche_count = sum(1 for c in cliches if c in text)
    # 扩展检测
    extended_cliches = ["心中涌起", "油然而生", "不由自主", "若有所思", "心头一紧", 
                        "嘴角上扬", "空气中弥漫", "时间仿佛静止", "深吸一口气",
                        "眉头紧锁", "不禁笑了", "恍然大悟", "五味杂陈"]
    cliche_count += sum(1 for c in extended_cliches if c in text)
    results["模板化表达计数"] = cliche_count
    if cliche_count > 10:
        alerts.append("模板化表达过多（{}处），需大幅替换为具体描写".format(cliche_count))
    elif cliche_count > 5:
        alerts.append("模板化表达偏多（{}处），建议替换".format(cliche_count))
    
    # 维度5：标点节奏
    punctuation_positions = [i for i, c in enumerate(clean_text) if c in '。，！？、；：""''…—']
    if len(punctuation_positions) >= 5:
        intervals = [punctuation_positions[i+1] - punctuation_positions[i] 
                     for i in range(len(punctuation_positions)-1)]
        if intervals:
            avg_interval = sum(intervals) / len(intervals)
            interval_var = sum((iv - avg_interval) ** 2 for iv in intervals) / len(intervals)
            interval_cv = math.sqrt(interval_var) / avg_interval if avg_interval > 0 else 0
            results["标点间隔变异系数"] = round(interval_cv, 3)
            if interval_cv < 0.3:
                alerts.append("标点节奏过于均匀（CV={:.3f}），需增加断句变化".format(interval_cv))
    
    # 维度6：对话比例
    dialogue_text = re.findall(r'["“”「」『』](.*?)["“”「」『』]', text)
    dialogue_chars = sum(len(d) for d in dialogue_text)
    dialogue_ratio = dialogue_chars / len(chars) if chars else 0
    results["对话占比"] = round(dialogue_ratio, 3)
    if dialogue_ratio < 0.05:
        alerts.append("对话占比过低（{:.1%}），文本偏叙述".format(dialogue_ratio))
    elif dialogue_ratio > 0.65:
        alerts.append("对话占比过高（{:.1%}），结构异常".format(dialogue_ratio))
    
    # 维度7：情绪词密度
    emotion_words = ["悲伤", "愤怒", "快乐", "幸福", "痛苦", "绝望", "恐惧", "焦虑",
                     "温暖", "感动", "心碎", "崩溃", "释然", "心疼", "委屈", "不甘",
                     "涌起", "蔓延", "袭来", "席卷", "吞噬", "笼罩", "弥漫", "充斥"]
    emotion_count = sum(text.count(w) for w in emotion_words)
    emotion_density = emotion_count / (len(chars) / 1000) if chars else 0
    results["情绪词密度_每千字"] = round(emotion_density, 1)
    if emotion_density > 8:
        alerts.append("情绪词密度过高（{:.1f}/千字），有刻意堆叠感".format(emotion_density))
    elif emotion_density < 1 and len(chars) > 5000:
        alerts.append("情绪词密度过低（{:.1f}/千字），文本偏冷".format(emotion_density))
    
    # 维度8：语义平滑度（简易版：相邻句相似度估算）
    # 用句首词的重复率作为代理指标——相邻句以相同词开头=平滑度高
    if len(sentences) >= 5:
        same_start = 0
        for i in range(len(sentences)-1):
            s1 = sentences[i].strip()[:2]
            s2 = sentences[i+1].strip()[:2]
            if s1 and s2 and s1 == s2:
                same_start += 1
        smooth_ratio = same_start / (len(sentences) - 1)
        results["相邻句同首词比例"] = round(smooth_ratio, 3)
        if smooth_ratio > 0.15:
            alerts.append("相邻句衔接过于平滑（同首词比例{:.1%}），需增加思维跳跃".format(smooth_ratio))
    
    # 综合风险评估
    risk_score = 0
    if ttr < 0.30: risk_score += 25
    elif ttr < 0.50: risk_score += 10
    if '句长标准差' in results and results['句长标准差'] < 3.0: risk_score += 20
    if '3gram高重复比例' in results and results['3gram高重复比例'] > 0.05: risk_score += 20
    if cliche_count > 10: risk_score += 15
    elif cliche_count > 5: risk_score += 8
    if '标点间隔变异系数' in results and results['标点间隔变异系数'] < 0.3: risk_score += 10
    if '相邻句同首词比例' in results and results['相邻句同首词比例'] > 0.15: risk_score += 10
    
    if risk_score >= 50:
        risk_level = "高风险 — 大概率被AIGC检测标记"
    elif risk_score >= 30:
        risk_level = "中风险 — 有较明显的AI统计特征"
    elif risk_score >= 15:
        risk_level = "低风险 — 有少量AI痕迹"
    else:
        risk_level = "安全 — 统计特征接近人类写作"
    
    results["AIGC风险评分"] = risk_score
    results["AIGC风险等级"] = risk_level
    
    return {
        "dimensions": results,
        "alerts": alerts,
        "risk_score": risk_score,
        "risk_level": risk_level
    }


def generate_report(result: dict) -> str:
    """生成可读的检测报告"""
    lines = []
    lines.append("=" * 50)
    lines.append("AI味检测报告")
    lines.append("=" * 50)
    lines.append(f"\n问题总数：{result['total_issues']}")
    lines.append(f"  严重：{result['severity_count']['严重']}")
    lines.append(f"  警告：{result['severity_count']['警告']}")
    lines.append(f"  提醒：{result['severity_count']['提醒']}")
    
    if result['rhythm']:
        lines.append(f"  节奏问题：{len(result['rhythm'])}处")
    
    # 评分（结合传统评分和AIGC风险评分）
    total = result['total_issues'] + len(result['rhythm'])
    if total == 0:
        score = "A+（未检测到AI味）"
    elif total <= 3:
        score = "A（轻微AI味）"
    elif total <= 8:
        score = "B（有一定AI味，建议润色）"
    elif total <= 15:
        score = "C（AI味较重，需要大改）"
    else:
        score = "D（AI味极重，建议重写）"
    
    lines.append(f"\nAI味评分：{score}")
    
    # AIGC检测维度分析
    if 'aigc_dimensions' in result and isinstance(result['aigc_dimensions'], dict):
        aigc = result['aigc_dimensions']
        if 'warning' in aigc:
            lines.append(f"\nAIGC维度分析：{aigc['warning']}")
        else:
            lines.append("\n" + "=" * 50)
            lines.append("AIGC检测维度分析（模拟平台检测逻辑）")
            lines.append("=" * 50)
            dims = aigc.get('dimensions', {})
            for key, value in dims.items():
                if key in ('3gram重复TOP5',):
                    # 特殊格式化
                    top5_str = ", ".join(f"「{g}」{c}次" for g, c in value) if value else "无"
                    lines.append(f"  {key}：{top5_str}")
                elif isinstance(value, float):
                    lines.append(f"  {key}：{value}")
                else:
                    lines.append(f"  {key}：{value}")
            
            lines.append(f"\n  风险评分：{aigc.get('risk_score', 'N/A')}")
            lines.append(f"  风险等级：{aigc.get('risk_level', 'N/A')}")
            
            if aigc.get('alerts'):
                lines.append("\n  ⚠ AIGC维度警告：")
                for alert in aigc['alerts']:
                    lines.append(f"    - {alert}")
    
    if result['issues']:
        lines.append("\n--- 问题详情 ---")
        for i, issue in enumerate(result['issues'], 1):
            lines.append(f"\n[{i}] 【{issue['severity']}】第{issue['line']}行")
            lines.append(f"    类型：{issue['type']}")
            lines.append(f"    发现：「{issue['found']}」")
            lines.append(f"    上下文：{issue['context']}")
            lines.append(f"    建议：{issue['suggestion']}")
    
    if result['rhythm']:
        lines.append("\n--- 节奏问题 ---")
        for i, r in enumerate(result['rhythm'], 1):
            lines.append(f"\n[{i}] 第{r['line']}行：{r['description']}")
    
    lines.append("\n" + "=" * 50)
    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python ai_taste_scanner.py <小说文本文件路径>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    text = Path(file_path).read_text(encoding="utf-8")
    result = detect_ai_flavor(text)
    report = generate_report(result)
    print(report)
    
    # 同时保存JSON格式供程序读取
    json_path = file_path.rsplit('.', 1)[0] + '_ai_scan.json'
    Path(json_path).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n详细检测结果已保存至：{json_path}")
