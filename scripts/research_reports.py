"""
研报管理模块
管理顶级投行研报链接，支持按股票/行业/主题分类
"""
import json
from datetime import datetime
from typing import List, Dict, Optional


class ResearchReportManager:
    """研报管理器"""

    def __init__(self, data_file: str = "data/research_reports.json"):
        self.data_file = data_file
        self.reports = self._load_reports()

    def _load_reports(self) -> Dict:
        """加载研报数据"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "reports": [],
                "tags": [],
                "sources": []
            }

    def add_report(self, report: Dict) -> bool:
        """添加研报"""
        required_fields = ["title", "date", "source", "url"]
        if not all(field in report for field in required_fields):
            return False

        report["id"] = len(self.reports["reports"]) + 1
        report["added_at"] = datetime.now().isoformat()
        self.reports["reports"].append(report)
        self._save_reports()
        return True

    def get_reports_by_stock(self, code: str) -> List[Dict]:
        """获取股票相关研报"""
        return [
            r for r in self.reports["reports"]
            if code in r.get("related_stocks", [])
        ]

    def get_reports_by_industry(self, industry: str) -> List[Dict]:
        """获取行业相关研报"""
        return [
            r for r in self.reports["reports"]
            if industry in r.get("industries", [])
        ]

    def get_reports_by_tag(self, tag: str) -> List[Dict]:
        """获取标签相关研报"""
        return [
            r for r in self.reports["reports"]
            if tag in r.get("tags", [])
        ]

    def search_reports(self, keyword: str) -> List[Dict]:
        """搜索研报"""
        keyword_lower = keyword.lower()
        return [
            r for r in self.reports["reports"]
            if keyword_lower in r.get("title", "").lower()
            or keyword_lower in r.get("summary", "").lower()
        ]

    def get_latest_reports(self, limit: int = 10) -> List[Dict]:
        """获取最新研报"""
        sorted_reports = sorted(
            self.reports["reports"],
            key=lambda x: x.get("date", ""),
            reverse=True
        )
        return sorted_reports[:limit]

    def _save_reports(self):
        """保存研报数据"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.reports, f, ensure_ascii=False, indent=2)


# ---- CLI ----

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="研报管理")
    parser.add_argument("--action", required=True, choices=[
        "add", "list", "search", "by-stock", "by-industry", "by-tag"
    ])
    parser.add_argument("--title", help="研报标题")
    parser.add_argument("--date", help="发布日期 (YYYY-MM-DD)")
    parser.add_argument("--source", help="来源 (Goldman Sachs, Morgan Stanley, etc.)")
    parser.add_argument("--url", help="研报链接")
    parser.add_argument("--stocks", help="相关股票代码（逗号分隔）")
    parser.add_argument("--industries", help="相关行业（逗号分隔）")
    parser.add_argument("--tags", help="标签（逗号分隔）")
    parser.add_argument("--summary", help="研报摘要")
    parser.add_argument("--keyword", help="搜索关键词")
    parser.add_argument("--code", help="股票代码")
    parser.add_argument("--industry", help="行业名称")
    parser.add_argument("--tag", help="标签")
    parser.add_argument("--limit", type=int, default=10, help="返回数量")

    args = parser.parse_args()

    manager = ResearchReportManager()

    if args.action == "add":
        report = {
            "title": args.title,
            "date": args.date,
            "source": args.source,
            "url": args.url,
            "related_stocks": args.stocks.split(",") if args.stocks else [],
            "industries": args.industries.split(",") if args.industries else [],
            "tags": args.tags.split(",") if args.tags else [],
            "summary": args.summary or ""
        }
        if manager.add_report(report):
            print(f"✅ 研报已添加：{args.title}")
        else:
            print("❌ 添加失败：缺少必填字段")

    elif args.action == "list":
        reports = manager.get_latest_reports(args.limit)
        print(json.dumps(reports, ensure_ascii=False, indent=2))

    elif args.action == "search":
        if not args.keyword:
            print("❌ 需要提供 --keyword 参数")
        else:
            reports = manager.search_reports(args.keyword)
            print(json.dumps(reports, ensure_ascii=False, indent=2))

    elif args.action == "by-stock":
        if not args.code:
            print("❌ 需要提供 --code 参数")
        else:
            reports = manager.get_reports_by_stock(args.code)
            print(json.dumps(reports, ensure_ascii=False, indent=2))

    elif args.action == "by-industry":
        if not args.industry:
            print("❌ 需要提供 --industry 参数")
        else:
            reports = manager.get_reports_by_industry(args.industry)
            print(json.dumps(reports, ensure_ascii=False, indent=2))

    elif args.action == "by-tag":
        if not args.tag:
            print("❌ 需要提供 --tag 参数")
        else:
            reports = manager.get_reports_by_tag(args.tag)
            print(json.dumps(reports, ensure_ascii=False, indent=2))
