#!/usr/bin/env node
/**
 * 🦞 Feishu PPT Generator - 专业 PPT 生成工具
 * 基于 PptxGenJS (⭐5.8k)
 * 
 * 用法:
 *   node ppt-generator.js --title "方案汇报" --output output.pptx
 *   node ppt-generator.js --template proposal --output output.pptx
 */

const PptxGenJS = require('pptxgenjs');
const fs = require('fs');
const path = require('path');

// ============================================================
// 配色方案
// ============================================================

const THEMES = {
  // 飞书品牌 - 蓝白
  feishu: {
    name: '飞书品牌',
    primary: '007AFF',
    secondary: '5856D6',
    accent: '34C759',
    dark: '1D1D1F',
    light: 'F5F5F7',
    white: 'FFFFFF',
    gray: '86868B',
    fontTitle: 'Arial',
    fontBody: 'Arial',
  },
  // 深海商务
  executive: {
    name: '深海商务',
    primary: '1E2761',
    secondary: 'CADCFC',
    accent: 'FFFFFF',
    dark: '0D1442',
    light: 'F0F4FF',
    white: 'FFFFFF',
    gray: '6B7280',
    fontTitle: 'Calibri',
    fontBody: 'Calibri',
  },
  // 科技
  tech: {
    name: '科技感',
    primary: '065A82',
    secondary: '1C7293',
    accent: '21295C',
    dark: '0D2B3E',
    light: 'E8F4F8',
    white: 'FFFFFF',
    gray: '7C8B9D',
    fontTitle: 'Calibri',
    fontBody: 'Calibri',
  },
  // 暖色方案
  warm: {
    name: '暖色商务',
    primary: 'B85042',
    secondary: 'E7E8D1',
    accent: 'A7BEAE',
    dark: '5C2C24',
    light: 'F7F4EF',
    white: 'FFFFFF',
    gray: '8B7D72',
    fontTitle: 'Georgia',
    fontBody: 'Calibri',
  },
};

// ============================================================
// 预设模板
// ============================================================

const TEMPLATES = {
  proposal: {
    name: '售前方案',
    slides: [
      { type: 'title', title: '售前技术方案', subtitle: '{{company}}', theme: 'executive' },
      { type: 'agenda', title: '议程', items: ['项目背景', '需求分析', '技术方案', '实施计划', '商务概览'] },
      { type: 'content', title: '项目背景', content: ['客户现状与挑战', '行业趋势分析', '项目目标'] },
      { type: 'content', title: '需求分析', content: ['业务需求', '技术要求', '非功能需求'] },
      { type: 'comparison', title: '方案对比', leftLabel: '现状', rightLabel: '优化后', leftItems: ['流程繁琐', '响应慢', '成本高'], rightItems: ['自动化', '实时响应', '降本30%'] },
      { type: 'content', title: '技术方案架构', content: ['整体架构设计', '核心组件', '数据流'] },
      { type: 'timeline', title: '实施计划', items: ['需求确认', '方案设计', 'PoC验证', '正式上线'] },
      { type: 'thankyou', title: '谢谢', subtitle: '期待合作' },
    ]
  },
  report: {
    name: '项目汇报',
    slides: [
      { type: 'title', title: '项目进展汇报', subtitle: '{{date}}', theme: 'tech' },
      { type: 'agenda', title: '汇报内容', items: ['项目概览', '关键进展', '风险与对策', '下一步计划'] },
      { type: 'stats', title: '关键数据', stats: [{value: '85%', label: '完成度'}, {value: '12', label: '里程碑'}, {value: '3', label: '风险项'}] },
      { type: 'content', title: '关键进展', content: ['里程碑1: 已完成', '里程碑2: 进行中', '里程碑3: 待启动'] },
      { type: 'two-column', title: '风险与对策', leftTitle: '风险', leftItems: ['进度风险', '资源风险'], rightTitle: '对策', rightItems: ['增加人手', '优先级调整'] },
      { type: 'thankyou', title: '谢谢', subtitle: 'Q&A' },
    ]
  },
  demo: {
    name: '产品演示',
    slides: [
      { type: 'title', title: '飞书 AI 解决方案', subtitle: '制造业数字化转型', theme: 'feishu' },
      { type: 'content', title: '行业痛点', content: ['生产数据分散', '协同效率低', '决策依赖经验', 'AI 落地难'] },
      { type: 'comparison', title: '飞书 AI 价值', leftLabel: '传统模式', rightLabel: '飞书 AI', leftItems: ['手动报表', '线下沟通', '事后分析'], rightItems: ['AI 自动生成', '即时协同', '实时预警'] },
      { type: 'stats', title: '客户收益', stats: [{value: '40%', label: '效率提升'}, {value: '60%', label: '响应加速'}, {value: '30%', label: '成本降低'}] },
      { type: 'timeline', title: '实施路径', items: ['需求调研', '方案设计', '系统部署', '培训上线'] },
      { type: 'thankyou', title: '感谢聆听', subtitle: 'www.feishu.cn' },
    ]
  }
};

// ============================================================
// PPT 生成器
// ============================================================

class FeishuPPT {
  constructor(themeName = 'feishu') {
    this.ppt = new PptxGenJS();
    this.theme = THEMES[themeName] || THEMES.feishu;
    this._setup();
  }

  _setup() {
    this.ppt.defineLayout({ name: 'WIDE', width: 13.33, height: 7.5 });
    this.ppt.layout = 'WIDE';
    this.ppt.author = 'Feishu AI FDE';
    this.ppt.company = 'Feishu';
    this.ppt.subject = 'Feishu AI 解决方案';
  }

  // ---- Slide Builders ----

  _titleSlide(data) {
    const slide = this.ppt.addSlide();
    slide.background = { fill: this.theme.dark };

    // 装饰线
    slide.addShape(this.ppt.ShapeType.rect, {
      x: 0, y: 0, w: 0.15, h: 7.5, fill: { color: this.theme.primary }
    });

    slide.addText(data.title, {
      x: 1.5, y: 2.0, w: 10, h: 1.8,
      fontSize: 44, fontFace: this.theme.fontTitle,
      color: this.theme.white, bold: true,
      align: 'left',
    });

    if (data.subtitle) {
      slide.addText(data.subtitle, {
        x: 1.5, y: 4.0, w: 10, h: 0.8,
        fontSize: 20, fontFace: this.theme.fontBody,
        color: this.theme.secondary,
        align: 'left',
      });
    }

    return slide;
  }

  _agendaSlide(data) {
    const slide = this.ppt.addSlide();
    slide.background = { fill: this.theme.white };

    this._addSectionTitle(slide, data.title);

    const items = data.items || [];
    const cols = Math.min(items.length, 6);
    const boxW = 10 / cols;
    const startX = (13.33 - boxW * cols) / 2;

    items.forEach((item, i) => {
      const x = startX + (i % cols) * boxW;
      const y = 2.5 + Math.floor(i / cols) * 2.5;

      slide.addShape(this.ppt.ShapeType.roundRect, {
        x, y, w: boxW - 0.4, h: 1.8,
        fill: { color: this.theme.light },
        rectRadius: 0.1,
      });

      slide.addText(`${i + 1}`, {
        x, y: y + 0.2, w: boxW - 0.4, h: 0.6,
        fontSize: 28, fontFace: this.theme.fontTitle,
        color: this.theme.primary, bold: true,
        align: 'center',
      });

      slide.addText(item, {
        x, y: y + 0.8, w: boxW - 0.4, h: 0.8,
        fontSize: 14, fontFace: this.theme.fontBody,
        color: this.theme.dark,
        align: 'center',
      });
    });

    return slide;
  }

  _contentSlide(data) {
    const slide = this.ppt.addSlide();
    slide.background = { fill: this.theme.white };
    this._addSectionTitle(slide, data.title);

    const items = data.content || [];
    const startY = 2.2;

    items.forEach((item, i) => {
      const y = startY + i * 1.2;

      // 序号圆点
      slide.addShape(this.ppt.ShapeType.ellipse, {
        x: 1.5, y: y + 0.1, w: 0.4, h: 0.4,
        fill: { color: this.theme.primary },
      });

      slide.addText(item, {
        x: 2.2, y, w: 9.5, h: 0.6,
        fontSize: 18, fontFace: this.theme.fontBody,
        color: this.theme.dark,
        align: 'left',
      });
    });

    return slide;
  }

  _comparisonSlide(data) {
    const slide = this.ppt.addSlide();
    slide.background = { fill: this.theme.white };
    this._addSectionTitle(slide, data.title);

    const midX = 6.665;

    // 左侧
    slide.addShape(this.ppt.ShapeType.roundRect, {
      x: 1, y: 2.2, w: 5.2, h: 4.5,
      fill: { color: 'FFF0F0' },
      rectRadius: 0.15,
    });
    slide.addText(data.leftLabel || '现状', {
      x: 1, y: 2.4, w: 5.2, h: 0.6,
      fontSize: 16, bold: true, color: 'FF3B30',
      align: 'center', fontFace: this.theme.fontTitle,
    });
    (data.leftItems || []).forEach((item, i) => {
      slide.addText(`✗ ${item}`, {
        x: 1.3, y: 3.2 + i * 0.7, w: 4.6, h: 0.5,
        fontSize: 14, color: '666666', fontFace: this.theme.fontBody,
      });
    });

    // 右侧
    slide.addShape(this.ppt.ShapeType.roundRect, {
      x: 7.1, y: 2.2, w: 5.2, h: 4.5,
      fill: { color: 'F0FFF4' },
      rectRadius: 0.15,
    });
    slide.addText(data.rightLabel || '优化后', {
      x: 7.1, y: 2.4, w: 5.2, h: 0.6,
      fontSize: 16, bold: true, color: '34C759',
      align: 'center', fontFace: this.theme.fontTitle,
    });
    (data.rightItems || []).forEach((item, i) => {
      slide.addText(`✓ ${item}`, {
        x: 7.4, y: 3.2 + i * 0.7, w: 4.6, h: 0.5,
        fontSize: 14, color: this.theme.dark, fontFace: this.theme.fontBody,
      });
    });

    return slide;
  }

  _statsSlide(data) {
    const slide = this.ppt.addSlide();
    slide.background = { fill: this.theme.dark };
    this._addSectionTitle(slide, data.title, this.theme.white);

    const stats = data.stats || [];
    const perW = 10 / stats.length;
    const startX = (13.33 - perW * stats.length) / 2;

    stats.forEach((s, i) => {
      const cx = startX + i * perW;

      slide.addText(s.value, {
        x: cx, y: 2.8, w: perW - 0.5, h: 1.5,
        fontSize: 48, fontFace: this.theme.fontTitle,
        color: this.theme.primary, bold: true,
        align: 'center',
      });

      slide.addText(s.label, {
        x: cx, y: 4.3, w: perW - 0.5, h: 0.6,
        fontSize: 16, fontFace: this.theme.fontBody,
        color: this.theme.secondary,
        align: 'center',
      });
    });

    return slide;
  }

  _timelineSlide(data) {
    const slide = this.ppt.addSlide();
    slide.background = { fill: this.theme.white };
    this._addSectionTitle(slide, data.title);

    const items = data.items || [];
    const totalW = 10;
    const startX = 1.5;
    const stepW = totalW / items.length;
    const lineY = 4.0;

    // 时间线
    slide.addShape(this.ppt.ShapeType.rect, {
      x: startX, y: lineY, w: totalW, h: 0.04,
      fill: { color: this.theme.primary },
    });

    items.forEach((item, i) => {
      const cx = startX + i * stepW + stepW / 2;

      // 节点
      slide.addShape(this.ppt.ShapeType.ellipse, {
        x: cx - 0.2, y: lineY - 0.18, w: 0.4, h: 0.4,
        fill: { color: this.theme.primary },
      });

      slide.addText(item, {
        x: cx - 1.5, y: lineY - 1.5, w: 3, h: 1.2,
        fontSize: 14, fontFace: this.theme.fontBody,
        color: this.theme.dark, align: 'center',
        valign: 'middle',
      });

      // 数字标签
      slide.addText(`${i + 1}`, {
        x: cx - 1.5, y: lineY + 0.5, w: 3, h: 0.6,
        fontSize: 12, fontFace: this.theme.fontBody,
        color: this.theme.gray, align: 'center',
      });
    });

    return slide;
  }

  _twoColumnSlide(data) {
    const slide = this.ppt.addSlide();
    slide.background = { fill: this.theme.white };
    this._addSectionTitle(slide, data.title);

    // 左列
    slide.addShape(this.ppt.ShapeType.roundRect, {
      x: 0.8, y: 2.2, w: 5.6, h: 4.5,
      fill: { color: this.theme.light }, rectRadius: 0.1,
    });
    slide.addText(data.leftTitle || '', {
      x: 1, y: 2.4, w: 5.2, h: 0.6,
      fontSize: 16, bold: true, color: this.theme.primary,
      align: 'center', fontFace: this.theme.fontTitle,
    });
    (data.leftItems || []).forEach((item, i) => {
      slide.addText(`• ${item}`, {
        x: 1.2, y: 3.2 + i * 0.7, w: 4.8, h: 0.5,
        fontSize: 14, color: this.theme.dark, fontFace: this.theme.fontBody,
      });
    });

    // 右列
    slide.addShape(this.ppt.ShapeType.roundRect, {
      x: 6.9, y: 2.2, w: 5.6, h: 4.5,
      fill: { color: this.theme.light }, rectRadius: 0.1,
    });
    slide.addText(data.rightTitle || '', {
      x: 7.1, y: 2.4, w: 5.2, h: 0.6,
      fontSize: 16, bold: true, color: this.theme.primary,
      align: 'center', fontFace: this.theme.fontTitle,
    });
    (data.rightItems || []).forEach((item, i) => {
      slide.addText(`• ${item}`, {
        x: 7.3, y: 3.2 + i * 0.7, w: 4.8, h: 0.5,
        fontSize: 14, color: this.theme.dark, fontFace: this.theme.fontBody,
      });
    });

    return slide;
  }

  _thankyouSlide(data) {
    const slide = this.ppt.addSlide();
    slide.background = { fill: this.theme.dark };

    slide.addText(data.title || '谢谢', {
      x: 1.5, y: 2.5, w: 10, h: 1.5,
      fontSize: 48, fontFace: this.theme.fontTitle,
      color: this.theme.white, bold: true,
      align: 'center',
    });

    if (data.subtitle) {
      slide.addText(data.subtitle, {
        x: 1.5, y: 4.2, w: 10, h: 0.8,
        fontSize: 20, fontFace: this.theme.fontBody,
        color: this.theme.secondary,
        align: 'center',
      });
    }

    return slide;
  }

  // ---- 辅助函数 ----

  _addSectionTitle(slide, title, color = null) {
    slide.addText(title, {
      x: 1, y: 0.5, w: 11, h: 1.0,
      fontSize: 28, fontFace: this.theme.fontTitle,
      color: color || this.theme.dark, bold: true,
      align: 'left',
    });

    slide.addShape(this.ppt.ShapeType.rect, {
      x: 1, y: 1.4, w: 1.5, h: 0.04,
      fill: { color: this.theme.primary },
    });
  }

  // ---- 主生成方法 ----

  generate(templateName, variables = {}, outputPath = 'output.pptx') {
    const template = TEMPLATES[templateName];
    if (!template) {
      console.error(`❌ 未知模板: ${templateName}`);
      console.log(`   可用模板: ${Object.keys(TEMPLATES).join(', ')}`);
      process.exit(1);
    }

    console.log(`📄 生成: ${template.name}`);
    
    template.slides.forEach((slideData, i) => {
      // 应用主题
      if (slideData.theme) {
        this.theme = THEMES[slideData.theme] || this.theme;
      }

      // 替换变量
      const processed = this._resolveVars(slideData, variables);

      // 构建幻灯片
      switch (processed.type) {
        case 'title': this._titleSlide(processed); break;
        case 'agenda': this._agendaSlide(processed); break;
        case 'content': this._contentSlide(processed); break;
        case 'comparison': this._comparisonSlide(processed); break;
        case 'stats': this._statsSlide(processed); break;
        case 'timeline': this._timelineSlide(processed); break;
        case 'two-column': this._twoColumnSlide(processed); break;
        case 'thankyou': this._thankyouSlide(processed); break;
        default:
          console.warn(`  跳过未知类型: ${processed.type}`);
      }

      console.log(`  第 ${i + 1} 页: ${processed.type} - ${processed.title}`);
    });

    this.ppt.writeFile({ fileName: outputPath }).then(() => {
      console.log(`\n✅ PPT 已生成: ${outputPath}`);
      console.log(`   共 ${template.slides.length} 页`);
    }).catch(err => {
      console.error(`❌ 生成失败: ${err.message}`);
    });
  }

  _resolveVars(data, vars) {
    const str = JSON.stringify(data);
    const resolved = str.replace(/\{\{(\w+)\}\}/g, (_, key) => {
      return vars[key] || `{{${key}}}`;
    });
    return JSON.parse(resolved);
  }

  // ---- 列表模板 ----

  static listTemplates() {
    console.log('\n📋 可用模板:\n');
    Object.entries(TEMPLATES).forEach(([key, t]) => {
      console.log(`  ${key.padEnd(12)} ${t.name}`);
      console.log(`  ${' '.repeat(12)} ${t.slides.length} 页: ${t.slides.map(s => s.type).join(' → ')}`);
      console.log();
    });
  }

  static listThemes() {
    console.log('\n🎨 配色方案:\n');
    Object.entries(THEMES).forEach(([key, t]) => {
      console.log(`  ${key.padEnd(12)} ${t.name}`);
    });
    console.log();
  }
}

// ============================================================
// CLI 入口
// ============================================================

if (require.main === module) {
  const args = process.argv.slice(2);
  
  if (args.includes('--list')) {
    FeishuPPT.listTemplates();
    FeishuPPT.listThemes();
    process.exit(0);
  }

  const getArg = (flag) => {
    const i = args.indexOf(flag);
    return i >= 0 ? args[i + 1] : null;
  };

  const template = getArg('--template') || 'proposal';
  const output = getArg('--output') || 'output.pptx';
  const theme = getArg('--theme') || 'feishu';
  const title = getArg('--title') || '';
  const company = getArg('--company') || '';
  const date = getArg('--date') || new Date().toLocaleDateString('zh-CN');

  const ppt = new FeishuPPT(theme);
  ppt.generate(template, { title, company, date }, output);
}

module.exports = { FeishuPPT, THEMES, TEMPLATES };
