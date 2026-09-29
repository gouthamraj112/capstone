import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ArrowStyle
import os

def create_architecture_diagram():
    fig = plt.figure(figsize=(20, 13), facecolor='#0B1118')
    ax = fig.add_subplot(111)
    ax.set_facecolor('#0B1118')
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Color Palette
    BG_DARK = '#0B1118'
    CARD_BG = '#131D28'
    CARD_BORDER = '#203247'
    CYAN_ACCENT = '#00F2FE'
    TEAL_ACCENT = '#4FACFE'
    GREEN_ACCENT = '#10B981'
    PURPLE_ACCENT = '#8B5CF6'
    AMBER_ACCENT = '#F59E0B'
    ROSE_ACCENT = '#F43F5E'
    TEXT_LIGHT = '#F8FAFC'
    TEXT_MUTED = '#94A3B8'
    TEXT_ACCENT = '#38BDF8'

    # Title & Subtitle
    ax.text(50, 97.2, "AI-POWERED SMART GRID ENERGY INTELLIGENCE ASSISTANT", 
            fontsize=20, fontweight='bold', ha='center', va='center', color=TEXT_LIGHT, fontfamily='sans-serif')
    ax.text(50, 94.6, "End-to-End System Architecture: Data Ingestion → Preprocessing → Storage → Analytics & ML → Multi-Agent System → User Delivery", 
            fontsize=11, ha='center', va='center', color=TEXT_ACCENT, fontfamily='sans-serif')

    # Helper function to draw rounded boxes
    def draw_box(x, y, w, h, title, subtitle, items=None, border_color=CARD_BORDER, bg_color=CARD_BG, title_color=TEXT_LIGHT):
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.5,rounding_size=1.2",
                             linewidth=1.5, edgecolor=border_color, facecolor=bg_color, zorder=2)
        ax.add_patch(box)
        
        # Header
        ax.text(x + w/2, y + h - 2.2, title, fontsize=11, fontweight='bold', ha='center', va='center', color=title_color, zorder=3)
        if subtitle:
            ax.text(x + w/2, y + h - 4.4, subtitle, fontsize=8.5, ha='center', va='center', color=TEXT_MUTED, zorder=3)
            
        # Items list
        if items:
            start_y = y + h - 6.8
            line_height = 2.0
            for i, itm in enumerate(items):
                ax.text(x + 1.5, start_y - (i * line_height), f"• {itm}", fontsize=8.2, ha='left', va='center', color=TEXT_LIGHT, zorder=3)

    # Helper for flow arrows
    def draw_arrow(x1, y1, x2, y2, color=CYAN_ACCENT, text="", text_offset=(0, 1.2)):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=2.0, mutation_scale=15),
                    zorder=4)
        if text:
            ax.text((x1 + x2)/2 + text_offset[0], (y1 + y2)/2 + text_offset[1], text,
                    fontsize=8.5, fontweight='bold', color=color, ha='center', va='center', zorder=5,
                    bbox=dict(boxstyle="round,pad=0.2", facecolor=BG_DARK, edgecolor='none', alpha=0.85))

    # =========================================================================
    # ROW 1 (Top): DATA INGESTION & STORAGE (Y: 76 - 91)
    # =========================================================================
    # 1. Dataset Box
    draw_box(4, 76, 26, 15, "1. UCI Smart Grid Dataset", "2,075,259 raw 1-minute measurements (~47 mo)",
             items=["Active & Reactive Power (kW, kVAR)",
                    "Voltage (V) & Global Intensity (A)",
                    "Sub-metering 1 (Kitchen / Dishwasher)",
                    "Sub-metering 2 (Laundry / Refrigeration)",
                    "Sub-metering 3 (Water-heater & AC)"],
             border_color=TEAL_ACCENT, title_color=TEAL_ACCENT)

    # Arrow 1 -> 2
    draw_arrow(30.5, 83.5, 36.5, 83.5, color=TEAL_ACCENT, text="Stream / Chunk")

    # 2. Data Preprocessing & Feature Engineering
    draw_box(37, 76, 27, 15, "2. Preprocessing & Feature Eng.", "Validation, Cleaning & Temporal Enrichment",
             items=["Parse local wall-clock dates & times",
                    "Handle '?' null values; drop corrupt rows",
                    "Interpolate short gaps (<=5 min active power)",
                    "Deduplicate records (keep latest reading)",
                    "Temporal features: hour, day, month, iso_week,",
                    "is_weekend, is_night, is_peak_hour (17-21)"],
             border_color=CYAN_ACCENT, title_color=CYAN_ACCENT)

    # Arrow 2 -> 3
    draw_arrow(64.5, 83.5, 70.5, 83.5, color=CYAN_ACCENT, text="Materialize")

    # 3. MongoDB Knowledge Base
    draw_box(71, 76, 25, 15, "3. MongoDB Knowledge Base", "High-Performance Indexed Collections",
             items=["energy_data: 2,075,259 cleaned rows",
                    "hourly_energy: 34,589 hourly aggregations",
                    "daily_energy: 1,442 daily demand records",
                    "anomalies: 3,097 tagged anomaly events",
                    "forecasts: Persisted forecast snapshots",
                    "agent_traces & query_history collections"],
             border_color=GREEN_ACCENT, title_color=GREEN_ACCENT)

    # Arrow Down to Layer 2
    draw_arrow(83.5, 75.5, 83.5, 68.5, color=GREEN_ACCENT, text="Indexed Querying")

    # =========================================================================
    # ROW 2 (Middle-Upper): ANALYTICAL & ML ENGINES (Y: 51 - 67)
    # =========================================================================
    # Section Header
    ax.text(50, 69.5, "CORE ANALYTICS, ANOMALY DETECTION & FORECASTING ENGINES", 
            fontsize=12, fontweight='bold', ha='center', va='center', color=AMBER_ACCENT)

    # ML 1: Consumption & Trends Analytics
    draw_box(4, 51, 28, 16, "Core Energy Analytics", "Statistical Aggregation & Pattern Profiling",
             items=["Diurnal Hourly Demand Profiles (top hours)",
                    "Weekday (1.036 kW) vs Weekend (1.234 kW)",
                    "Evening Peak Surge: 18:00-21:00 (+51.4%)",
                    "Top peak ranking (observed max: 11.122 kW)",
                    "Monthly & seasonal variation trends"],
             border_color=AMBER_ACCENT, title_color=AMBER_ACCENT)

    # ML 2: Anomaly Detection Engine
    draw_box(36, 51, 28, 16, "Robust Anomaly Detection", "Rolling Median Absolute Deviation (MAD)",
             items=["24-hour rolling median baseline window",
                    "Robust Z-score scaling: (demand - med) / MAD",
                    "Threshold: score > 3.5 flags anomalies",
                    "Severity categorization: Low, Medium, High",
                    "Transparent explainability & reason codes",
                    "Controlled spike validation: Precision/Recall/F1"],
             border_color=ROSE_ACCENT, title_color=ROSE_ACCENT)

    # ML 3: Time-Series Forecasting Engine
    draw_box(68, 51, 28, 16, "Time-Series Forecasting", "Seasonal-Naive Baseline & Uncertainty Bands",
             items=["Captures strong 24-hour diurnal cyclicity",
                    "Horizon support: 1 to 168 hours ahead",
                    "Empirical prediction intervals (+/- 1.96 MAD)",
                    "Chronological holdout validation (24-hour)",
                    "Evaluation metrics: MAE, RMSE, MAPE",
                    "Zero-future leakage train/test split"],
             border_color=PURPLE_ACCENT, title_color=PURPLE_ACCENT)

    # Arrows from ML to Agents
    draw_arrow(18, 50.5, 18, 44.5, color=AMBER_ACCENT)
    draw_arrow(50, 50.5, 50, 44.5, color=ROSE_ACCENT)
    draw_arrow(82, 50.5, 82, 44.5, color=PURPLE_ACCENT)

    # =========================================================================
    # ROW 3 (Middle): MULTI-AGENT INTELLIGENCE WORKFLOW (Y: 26 - 43)
    # =========================================================================
    # Multi-Agent Box Outer Boundary
    outer_agent_box = FancyBboxPatch((2, 25), 96, 18.5, boxstyle="round,pad=0.5,rounding_size=1.5",
                                     linewidth=2.0, edgecolor=CYAN_ACCENT, facecolor='#0D1926', zorder=1)
    ax.add_patch(outer_agent_box)
    ax.text(50, 42.0, "SPECIALIZED MULTI-AGENT ENERGY INTELLIGENCE WORKFLOW (A2A Communication & Structured Contracts)",
            fontsize=11.5, fontweight='bold', ha='center', va='center', color=CYAN_ACCENT, zorder=3)

    # Agent 1: Energy Data Analysis Agent
    draw_box(4, 27, 16.5, 13, "Data Analysis Agent", "Historical Patterns",
             items=["Hourly / diurnal stats",
                    "Weekday / weekend",
                    "Top 10 ranked peaks",
                    "Emits structured fact msg"],
             border_color='#38BDF8', title_color='#38BDF8')

    # Agent 2: Anomaly Detection Agent
    draw_box(23, 27, 16.5, 13, "Anomaly Agent", "Outlier Evidence",
             items=["Detects sudden spikes",
                    "Assigns severity tags",
                    "Calculates deviation",
                    "Emits anomaly evidence"],
             border_color=ROSE_ACCENT, title_color=ROSE_ACCENT)

    # Agent 3: Forecasting Agent
    draw_box(42, 27, 16.5, 13, "Forecasting Agent", "Demand Predictions",
             items=["Generates N-hr forecast",
                    "Computes lower/upper bounds",
                    "Evaluates horizon trends",
                    "Emits forecast array"],
             border_color=PURPLE_ACCENT, title_color=PURPLE_ACCENT)

    # Agent Handoff / A2A Arrows to Insight Agent
    draw_arrow(20.8, 33.5, 60.5, 33.5, color=CYAN_ACCENT)
    draw_arrow(39.8, 33.5, 60.5, 33.5, color=CYAN_ACCENT)
    draw_arrow(58.8, 33.5, 60.5, 33.5, color=CYAN_ACCENT)

    # Agent 4: Energy Insight Agent
    draw_box(61, 27, 16.5, 13, "Insight Agent", "Cross-Agent Synthesis",
             items=["Aggregates evidence",
                    "Synthesizes cross-metrics",
                    "Computes confidence score",
                    "Hands off to Decision"],
             border_color=GREEN_ACCENT, title_color=GREEN_ACCENT)

    # Arrow Insight -> Decision Support
    draw_arrow(78.0, 33.5, 80.5, 33.5, color=GREEN_ACCENT)

    # Agent 5: Decision Support Agent
    draw_box(81, 27, 16.0, 13, "Decision Agent", "Operational Support",
             items=["Peak shaving alerts",
                    "Load shifting strategies",
                    "Equipment inspection",
                    "Data-backed actions"],
             border_color=AMBER_ACCENT, title_color=AMBER_ACCENT)

    # Arrow Down to Layer 4
    draw_arrow(50, 24.5, 50, 19.5, color=CYAN_ACCENT, text="Traceability & Evidence Bundle")

    # =========================================================================
    # ROW 4 (Bottom): APPLICATION & USER DELIVERY LAYER (Y: 2 - 18)
    # =========================================================================
    # Evidence & Guardrails
    draw_box(4, 2.5, 27, 15.5, "Evidence Grounding & Security", "Zero-Hallucination Guardrails",
             items=["Prompt injection defense & input sanitization",
                    "Strict evidence verification: numbers_are_evidence_backed",
                    "Deterministic local fallback (works without OpenAI key)",
                    "Multilingual intent routing (EN, ES, FR, DE, ZH, HI)",
                    "Persisted audit trail in agent_traces collection"],
             border_color='#38BDF8', title_color='#38BDF8')

    # Arrow Guardrails -> API
    draw_arrow(31.5, 10.2, 36.5, 10.2, color='#38BDF8')

    # FastAPI Microservice
    draw_box(37, 2.5, 26, 15.5, "FastAPI Microservice", "Modular REST API Backend (:8000)",
             items=["GET /api/dashboard (KPIs & coverage)",
                    "GET /api/energy/* (trends, peaks, hourly, daily)",
                    "GET /api/anomalies (detected events & detail)",
                    "GET /api/forecast?hours=N (seasonal forecast)",
                    "POST /api/query (evidence-backed NL chat)",
                    "POST /api/agents/run & GET /api/agents/trace/{id}"],
             border_color=GREEN_ACCENT, title_color=GREEN_ACCENT)

    # Arrow API -> React UI
    draw_arrow(63.5, 10.2, 69.5, 10.2, color=GREEN_ACCENT, text="JSON API")

    # React + Vite Frontend
    draw_box(70, 2.5, 26, 15.5, "React + Vite SPA Frontend", "Modern Interactive UI (:5173)",
             items=["Overview Dashboard: KPIs, active power, voltage",
                    "Energy Analytics: diurnal curves, peak rankings",
                    "Anomaly Detection: interactive timeline & severity",
                    "Demand Forecast: horizon charts & error bands",
                    "AI Assistant Chat: evidence badges & trace viewer",
                    "Model Evaluation: MAE, RMSE, MAPE, precision/recall"],
             border_color=TEAL_ACCENT, title_color=TEAL_ACCENT)

    plt.tight_layout()
    
    os.makedirs('architecture', exist_ok=True)
    
    # Save High-Res JPEG
    jpg_path = os.path.join('architecture', 'architecture_diagram.jpg')
    plt.savefig(jpg_path, format='jpg', dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')
    print(f"Saved JPEG: {jpg_path}")

    # Save Vector PDF
    pdf_path = os.path.join('architecture', 'architecture_diagram.pdf')
    plt.savefig(pdf_path, format='pdf', bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')
    print(f"Saved PDF: {pdf_path}")

    plt.close()

if __name__ == '__main__':
    create_architecture_diagram()
