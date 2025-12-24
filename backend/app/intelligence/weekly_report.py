"""
Automated weekly report generator.
Generates comprehensive reports on opportunities and sends them via email/Slack/Discord.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import json


@dataclass
class WeeklyReport:
    """Weekly report structure."""
    report_id: str
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    summary: Dict[str, Any]
    highlights: List[Dict[str, Any]]
    new_opportunities: List[Dict[str, Any]]
    status_changes: List[Dict[str, Any]]
    top_scored: List[Dict[str, Any]]
    upcoming_deadlines: List[Dict[str, Any]]
    recommendations: List[str]
    metrics: Dict[str, Any]
    html_content: str
    markdown_content: str


class WeeklyReportGenerator:
    """Generates automated weekly reports."""
    
    def __init__(self):
        self.last_report_date: Optional[datetime] = None
    
    async def generate_report(
        self,
        opportunities: List[Dict[str, Any]],
        period_days: int = 7
    ) -> WeeklyReport:
        """
        Generate a comprehensive weekly report.
        
        Args:
            opportunities: All opportunities to analyze
            period_days: Number of days to include in report
            
        Returns:
            WeeklyReport with all analysis and formatted content
        """
        now = datetime.now()
        period_start = now - timedelta(days=period_days)
        period_end = now
        
        # Filter opportunities by period
        new_in_period = self._filter_by_date(opportunities, period_start, "created_at")
        
        # Analyze status changes
        status_changes = self._get_status_changes(opportunities, period_start)
        
        # Get top scored
        top_scored = sorted(
            opportunities,
            key=lambda x: x.get("score", 0),
            reverse=True
        )[:10]
        
        # Get upcoming deadlines
        upcoming_deadlines = self._get_upcoming_deadlines(opportunities, days=14)
        
        # Calculate metrics
        metrics = self._calculate_metrics(opportunities, new_in_period, period_days)
        
        # Generate highlights
        highlights = self._generate_highlights(
            new_in_period, 
            top_scored, 
            upcoming_deadlines,
            metrics
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(metrics, opportunities)
        
        # Generate formatted content
        html_content = self._generate_html(
            period_start, period_end, 
            metrics, highlights, 
            new_in_period, top_scored, 
            upcoming_deadlines, recommendations
        )
        
        markdown_content = self._generate_markdown(
            period_start, period_end,
            metrics, highlights,
            new_in_period, top_scored,
            upcoming_deadlines, recommendations
        )
        
        report = WeeklyReport(
            report_id=f"report-{now.strftime('%Y%m%d-%H%M%S')}",
            generated_at=now,
            period_start=period_start,
            period_end=period_end,
            summary={
                "total_opportunities": len(opportunities),
                "new_this_period": len(new_in_period),
                "status_changes": len(status_changes),
                "upcoming_deadlines": len(upcoming_deadlines),
            },
            highlights=highlights,
            new_opportunities=new_in_period[:20],
            status_changes=status_changes[:20],
            top_scored=top_scored,
            upcoming_deadlines=upcoming_deadlines,
            recommendations=recommendations,
            metrics=metrics,
            html_content=html_content,
            markdown_content=markdown_content
        )
        
        self.last_report_date = now
        return report
    
    def _filter_by_date(
        self,
        opportunities: List[Dict[str, Any]],
        since: datetime,
        date_field: str
    ) -> List[Dict[str, Any]]:
        """Filter opportunities by date field."""
        result = []
        for opp in opportunities:
            date_str = opp.get(date_field)
            if date_str:
                try:
                    opp_date = datetime.fromisoformat(date_str.replace("Z", "+00:00")).replace(tzinfo=None)
                    if opp_date >= since:
                        result.append(opp)
                except:
                    pass
        return result
    
    def _get_status_changes(
        self,
        opportunities: List[Dict[str, Any]],
        since: datetime
    ) -> List[Dict[str, Any]]:
        """Get opportunities with recent status changes."""
        changes = []
        for opp in opportunities:
            updated = opp.get("updated_at")
            if updated:
                try:
                    update_date = datetime.fromisoformat(updated.replace("Z", "+00:00")).replace(tzinfo=None)
                    if update_date >= since and opp.get("status") != "new":
                        changes.append({
                            "id": opp.get("id"),
                            "title": opp.get("title"),
                            "status": opp.get("status"),
                            "updated_at": updated
                        })
                except:
                    pass
        return changes
    
    def _get_upcoming_deadlines(
        self,
        opportunities: List[Dict[str, Any]],
        days: int = 14
    ) -> List[Dict[str, Any]]:
        """Get opportunities with upcoming deadlines."""
        now = datetime.now()
        cutoff = now + timedelta(days=days)
        
        upcoming = []
        for opp in opportunities:
            deadline = opp.get("deadline_at")
            if deadline and opp.get("status") not in ["won", "lost", "archived"]:
                try:
                    deadline_date = datetime.fromisoformat(deadline.replace("Z", "+00:00")).replace(tzinfo=None)
                    if now <= deadline_date <= cutoff:
                        days_left = (deadline_date - now).days
                        upcoming.append({
                            **opp,
                            "days_until_deadline": days_left,
                            "urgency": "critical" if days_left <= 3 else "high" if days_left <= 7 else "normal"
                        })
                except:
                    pass
        
        return sorted(upcoming, key=lambda x: x["days_until_deadline"])
    
    def _calculate_metrics(
        self,
        all_opportunities: List[Dict[str, Any]],
        new_opportunities: List[Dict[str, Any]],
        period_days: int
    ) -> Dict[str, Any]:
        """Calculate key performance metrics."""
        # Status distribution
        status_counts = {}
        for opp in all_opportunities:
            status = opp.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Score distribution
        scores = [opp.get("score", 0) for opp in all_opportunities]
        avg_score = sum(scores) / len(scores) if scores else 0
        high_score_count = len([s for s in scores if s >= 7])
        
        # Budget analysis
        budgets = [
            opp.get("budget_amount", 0) 
            for opp in all_opportunities 
            if opp.get("budget_amount")
        ]
        total_budget = sum(budgets)
        avg_budget = total_budget / len(budgets) if budgets else 0
        
        # Source distribution
        source_counts = {}
        for opp in all_opportunities:
            source = opp.get("source_type", "unknown")
            source_counts[source] = source_counts.get(source, 0) + 1
        
        # Conversion metrics
        won = status_counts.get("won", 0)
        lost = status_counts.get("lost", 0)
        conversion_rate = won / (won + lost) if (won + lost) > 0 else 0
        
        # Growth rate
        daily_rate = len(new_opportunities) / period_days if period_days > 0 else 0
        
        return {
            "total_count": len(all_opportunities),
            "new_count": len(new_opportunities),
            "daily_rate": round(daily_rate, 2),
            "status_distribution": status_counts,
            "average_score": round(avg_score, 2),
            "high_score_count": high_score_count,
            "total_budget_value": total_budget,
            "average_budget": round(avg_budget, 2),
            "source_distribution": source_counts,
            "conversion_rate": round(conversion_rate * 100, 1),
            "won_count": won,
            "lost_count": lost,
        }
    
    def _generate_highlights(
        self,
        new_opps: List[Dict[str, Any]],
        top_scored: List[Dict[str, Any]],
        upcoming: List[Dict[str, Any]],
        metrics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate key highlights for the report."""
        highlights = []
        
        # New opportunities highlight
        if new_opps:
            highlights.append({
                "type": "new",
                "icon": "📥",
                "title": f"{len(new_opps)} nouvelles opportunités",
                "description": "Ajoutées cette semaine",
                "priority": "info"
            })
        
        # High score opportunities
        high_scored = [o for o in new_opps if o.get("score", 0) >= 7]
        if high_scored:
            highlights.append({
                "type": "high_score",
                "icon": "⭐",
                "title": f"{len(high_scored)} opportunités à fort potentiel",
                "description": "Score ≥ 7/10",
                "priority": "success"
            })
        
        # Urgent deadlines
        critical = [o for o in upcoming if o.get("urgency") == "critical"]
        if critical:
            highlights.append({
                "type": "deadline",
                "icon": "⚠️",
                "title": f"{len(critical)} deadlines critiques",
                "description": "Dans les 3 prochains jours",
                "priority": "warning"
            })
        
        # Conversion rate
        if metrics["conversion_rate"] > 0:
            highlights.append({
                "type": "conversion",
                "icon": "📈",
                "title": f"Taux de conversion: {metrics['conversion_rate']}%",
                "description": f"{metrics['won_count']} gagnées / {metrics['won_count'] + metrics['lost_count']} finalisées",
                "priority": "info"
            })
        
        # Budget potential
        if metrics["total_budget_value"] > 0:
            budget_str = f"{metrics['total_budget_value']:,.0f}€".replace(",", " ")
            highlights.append({
                "type": "budget",
                "icon": "💰",
                "title": f"Potentiel total: {budget_str}",
                "description": "Valeur cumulée des opportunités",
                "priority": "info"
            })
        
        return highlights
    
    def _generate_recommendations(
        self,
        metrics: Dict[str, Any],
        opportunities: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Score-based
        if metrics["average_score"] < 5:
            recommendations.append(
                "Le score moyen est faible - revoir les critères de collecte"
            )
        elif metrics["high_score_count"] >= 5:
            recommendations.append(
                f"Prioriser les {metrics['high_score_count']} opportunités à score élevé"
            )
        
        # Volume-based
        if metrics["daily_rate"] < 1:
            recommendations.append(
                "Faible volume de nouvelles opportunités - activer plus de sources"
            )
        
        # Source diversity
        sources = metrics.get("source_distribution", {})
        if len(sources) < 3:
            recommendations.append(
                "Diversifier les sources de collecte pour plus d'opportunités"
            )
        
        # Status-based
        status = metrics.get("status_distribution", {})
        new_count = status.get("new", 0)
        if new_count > 20:
            recommendations.append(
                f"{new_count} opportunités en attente de traitement - planifier une session de tri"
            )
        
        # Conversion-based
        if metrics["conversion_rate"] < 10 and metrics["lost_count"] > 5:
            recommendations.append(
                "Taux de conversion faible - analyser les causes de perte"
            )
        
        return recommendations[:5]
    
    def _generate_html(
        self,
        period_start: datetime,
        period_end: datetime,
        metrics: Dict[str, Any],
        highlights: List[Dict[str, Any]],
        new_opps: List[Dict[str, Any]],
        top_scored: List[Dict[str, Any]],
        upcoming: List[Dict[str, Any]],
        recommendations: List[str]
    ) -> str:
        """Generate HTML formatted report."""
        period_str = f"{period_start.strftime('%d/%m/%Y')} - {period_end.strftime('%d/%m/%Y')}"
        
        highlights_html = "".join([
            f'''
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 10px 0;">
                <span style="font-size: 24px;">{h['icon']}</span>
                <strong>{h['title']}</strong><br>
                <small style="color: #666;">{h['description']}</small>
            </div>
            '''
            for h in highlights
        ])
        
        top_scored_html = "".join([
            f'''
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #eee;">{o.get('title', 'N/A')[:50]}</td>
                <td style="padding: 8px; border-bottom: 1px solid #eee;">{o.get('organization', 'N/A')}</td>
                <td style="padding: 8px; border-bottom: 1px solid #eee; font-weight: bold;">{o.get('score', 0)}/10</td>
            </tr>
            '''
            for o in top_scored[:5]
        ])
        
        upcoming_html = "".join([
            f'''
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #eee;">{o.get('title', 'N/A')[:50]}</td>
                <td style="padding: 8px; border-bottom: 1px solid #eee;">
                    <span style="color: {'red' if o.get('urgency') == 'critical' else 'orange'};">
                        {o.get('days_until_deadline', '?')} jours
                    </span>
                </td>
            </tr>
            '''
            for o in upcoming[:5]
        ])
        
        recommendations_html = "".join([
            f"<li style='margin: 5px 0;'>{r}</li>"
            for r in recommendations
        ])
        
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Rapport Hebdomadaire - Opportunities Radar</title>
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 12px; margin-bottom: 30px;">
                <h1 style="margin: 0;">📊 Rapport Hebdomadaire</h1>
                <p style="margin: 10px 0 0 0; opacity: 0.9;">{period_str}</p>
            </div>
            
            <h2>🎯 Points clés</h2>
            {highlights_html}
            
            <h2>📈 Métriques</h2>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px;">
                <div style="background: #e3f2fd; padding: 20px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 32px; font-weight: bold;">{metrics['new_count']}</div>
                    <div style="color: #666;">Nouvelles</div>
                </div>
                <div style="background: #e8f5e9; padding: 20px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 32px; font-weight: bold;">{metrics['high_score_count']}</div>
                    <div style="color: #666;">Score élevé</div>
                </div>
                <div style="background: #fff3e0; padding: 20px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 32px; font-weight: bold;">{metrics['conversion_rate']}%</div>
                    <div style="color: #666;">Conversion</div>
                </div>
            </div>
            
            <h2>⭐ Top Opportunités</h2>
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background: #f5f5f5;">
                        <th style="padding: 10px; text-align: left;">Titre</th>
                        <th style="padding: 10px; text-align: left;">Organisation</th>
                        <th style="padding: 10px; text-align: left;">Score</th>
                    </tr>
                </thead>
                <tbody>{top_scored_html}</tbody>
            </table>
            
            <h2>⏰ Deadlines Proches</h2>
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background: #f5f5f5;">
                        <th style="padding: 10px; text-align: left;">Titre</th>
                        <th style="padding: 10px; text-align: left;">Échéance</th>
                    </tr>
                </thead>
                <tbody>{upcoming_html}</tbody>
            </table>
            
            <h2>💡 Recommandations</h2>
            <ul style="background: #f8f9fa; padding: 20px 40px; border-radius: 8px;">
                {recommendations_html}
            </ul>
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; color: #666; font-size: 12px;">
                <p>Généré automatiquement par Opportunities Radar</p>
            </div>
        </body>
        </html>
        '''
    
    def _generate_markdown(
        self,
        period_start: datetime,
        period_end: datetime,
        metrics: Dict[str, Any],
        highlights: List[Dict[str, Any]],
        new_opps: List[Dict[str, Any]],
        top_scored: List[Dict[str, Any]],
        upcoming: List[Dict[str, Any]],
        recommendations: List[str]
    ) -> str:
        """Generate Markdown formatted report."""
        period_str = f"{period_start.strftime('%d/%m/%Y')} - {period_end.strftime('%d/%m/%Y')}"
        
        highlights_md = "\n".join([
            f"- {h['icon']} **{h['title']}** - {h['description']}"
            for h in highlights
        ])
        
        top_scored_md = "\n".join([
            f"| {o.get('title', 'N/A')[:40]} | {o.get('organization', 'N/A')[:20]} | {o.get('score', 0)}/10 |"
            for o in top_scored[:5]
        ])
        
        upcoming_md = "\n".join([
            f"| {o.get('title', 'N/A')[:40]} | {o.get('days_until_deadline', '?')} jours |"
            for o in upcoming[:5]
        ])
        
        recommendations_md = "\n".join([
            f"- {r}" for r in recommendations
        ])
        
        return f'''# 📊 Rapport Hebdomadaire
**Période:** {period_str}

---

## 🎯 Points Clés

{highlights_md}

---

## 📈 Métriques

| Métrique | Valeur |
|----------|--------|
| Nouvelles opportunités | {metrics['new_count']} |
| Score moyen | {metrics['average_score']}/10 |
| Opportunités score élevé | {metrics['high_score_count']} |
| Taux de conversion | {metrics['conversion_rate']}% |
| Total opportunités | {metrics['total_count']} |

---

## ⭐ Top Opportunités

| Titre | Organisation | Score |
|-------|--------------|-------|
{top_scored_md}

---

## ⏰ Deadlines Proches

| Titre | Échéance |
|-------|----------|
{upcoming_md}

---

## 💡 Recommandations

{recommendations_md}

---

*Généré automatiquement par Opportunities Radar*
'''


# Singleton instance
weekly_report_generator = WeeklyReportGenerator()
