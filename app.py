import streamlit as st
import json
import pandas as pd
from src.pipeline import ScholarshipPipeline
from src.models import SourceType

# -------------------------------------------------------------
# PAGE CONFIGURATION & THEMING
# -------------------------------------------------------------
st.set_page_config(
    page_title="Scholarship Intelligence Engine",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Sleek Modern Styling
st.markdown("""
<style>
    /* Global Container Adjustments */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    
    /* Custom Card Containers */
    .metric-card {
        background: #1e222d;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #2e3440;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        text-align: center;
    }
    
    .status-badge-verified {
        color: #43b581;
        background-color: rgba(67, 181, 129, 0.15);
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 600;
        border: 1px solid #43b581;
    }
    
    .status-badge-review {
        color: #faa61a;
        background-color: rgba(250, 166, 26, 0.15);
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 600;
        border: 1px solid #faa61a;
    }
    
    .status-badge-suspect {
        color: #f04747;
        background-color: rgba(240, 71, 71, 0.15);
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 600;
        border: 1px solid #f04747;
    }

    /* Subheader Styling */
    .section-header {
        font-size: 1.25rem;
        font-weight: 700;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        color: #eceff4;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Core Pipeline
@st.cache_resource
def load_pipeline():
    return ScholarshipPipeline()

pipeline = load_pipeline()

# -------------------------------------------------------------
# SIDEBAR CONTROL PANEL
# -------------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/graduation-cap.png", width=70)
    st.title("Intelligence Hub")
    st.caption("AI-Powered Fraud Screening & Extraction Engine")
    st.divider()
    
    st.markdown("### ⚙️ Engine Parameters")
    url_input = st.text_input("Target Portal URL", "https://scholarships.gov.in/")
    provider_input = st.text_input("Authority / Provider", "Government of India")
    
    source_type_str = st.selectbox(
        "Authority Level",
        ["GOVERNMENT", "UNIVERSITY", "TRUSTED_AGGREGATOR", "CORPORATE", "UNKNOWN"],
        help="Higher authority levels grant higher baseline trust scores."
    )
    
    st.divider()
    run_btn = st.button("🚀 Execute Analysis Pipeline", use_container_width=True, type="primary")

# -------------------------------------------------------------
# MAIN DASHBOARD INTERFACE
# -------------------------------------------------------------
st.title("🎓 Scholarship Verification & Intelligence Platform")
st.markdown("Crawl web pages, extract traceable evidence quotes, screen for fraudulent indicators, and compute dynamic confidence scores.")

if run_btn:
    if not url_input:
        st.error("⚠️ Please specify a target URL to continue.")
    else:
        with st.spinner("🕷️ Crawling DOM structure, parsing evidence, and executing anomaly heuristics..."):
            source_enum = SourceType[source_type_str]
            result = pipeline.process_url(
                url=url_input,
                default_provider=provider_input,
                source_type=source_enum
            )

        if "error" in result:
            st.error(f"❌ Pipeline Execution Failed: {result['error']}")
        else:
            st.toast("Analysis Complete!", icon="🎉")
            
            # Extract Metrics
            score = result.get("confidence_score", 0.0)
            status = result.get("status", "UNKNOWN")
            db_id = result.get("id", "N/A")
            record = result.get("record", {})
            evidence_list = record.get("evidence_list", [])

            # High-Level Metrics Row
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("Database Key", f"ID #{db_id}")
            with m2:
                # Dynamic Status Rendering
                if status == "VERIFIED":
                    badge_html = f'<span class="status-badge-verified">✓ {status}</span>'
                elif status == "NEEDS_REVIEW":
                    badge_html = f'<span class="status-badge-review">⚠️ {status}</span>'
                else:
                    badge_html = f'<span class="status-badge-suspect">🚫 {status}</span>'
                
                st.markdown("**Verification Status**")
                st.markdown(badge_html, unsafe_allow_html=True)
            with m3:
                st.metric("Confidence Score", f"{score} / 100")
                st.progress(min(int(score), 100))
            with m4:
                st.metric("Evidence Quotes", len(evidence_list))

            st.divider()

            # Tabbed View for Structured Results
            tab1, tab2, tab3, tab4 = st.tabs([
                "📋 Extracted Attributes", 
                "🕵️ Audit Evidence Quotes", 
                "🚨 Anomaly & Safety Flags", 
                "💾 Raw Data & Export"
            ])

            # TAB 1: EXTRACTED ATTRIBUTES
            with tab1:
                st.markdown("### 🏛️ Extracted Listing Metadata")
                
                col_left, col_right = st.columns(2)
                
                with col_left:
                    st.text_input("Scholarship Title", record.get("scholarship_name", "N/A"), disabled=True)
                    st.text_input("Provider / Authority", record.get("provider", "N/A"), disabled=True)
                    st.text_input("Funding Amount", record.get("amount") or "Not Specified", disabled=True)
                    
                with col_right:
                    st.text_input("Closing Deadline", record.get("closing_date") or "Not Specified", disabled=True)
                    st.text_input("Income Criteria", record.get("income_criteria") or "Not Specified", disabled=True)
                    st.text_input("Application URL", record.get("application_url") or "N/A", disabled=True)

                st.markdown("#### 📜 Eligibility Snippet")
                st.caption(record.get("eligibility") or "No eligibility snippet available.")

            # TAB 2: AUDIT EVIDENCE QUOTES
            with tab2:
                st.markdown("### 🔍 Traceable DOM Field Evidence")
                st.caption("Verbatim text quotes extracted directly from the HTML source code to guarantee audit transparency.")
                
                if evidence_list:
                    for i, ev in enumerate(evidence_list, 1):
                        with st.expander(f"📍 Evidence #{i} — Field: `{ev.field_name}`", expanded=True if i==1 else False):
                            st.write(f"**Extracted Value:** `{ev.field_value}`")
                            st.info(f"**Verbatim HTML Quote:** \"{ev.evidence_text}\"")
                else:
                    st.warning("No explicit evidence quotes were mapped for this record.")

            # TAB 3: ANOMALY & SAFETY FLAGS
            with tab3:
                st.markdown("### 🛡️ Fraud & Risk Diagnostic")
                
                flags = result.get("flags", [])
                warnings = result.get("warnings", [])
                
                c1, c2 = st.columns(2)
                
                with c1:
                    st.markdown("#### 🚨 Anomaly Flags (Critical)")
                    if flags:
                        for flag in flags:
                            st.error(f"• {flag}")
                    else:
                        st.success("Zero anomaly flags detected. No scam patterns identified.")
                        
                with c2:
                    st.markdown("#### ⚠️ Quality Warnings")
                    if warnings:
                        for warn in warnings:
                            st.warning(f"• {warn}")
                    else:
                        st.success("Zero data quality warnings logged.")

            # TAB 4: RAW DATA & EXPORT
            with tab4:
                st.markdown("### 📄 Exportable Intelligence Schema")
                
                export_data = {
                    "database_id": db_id,
                    "confidence_score": score,
                    "status": status,
                    "flags": flags,
                    "warnings": warnings,
                    "extracted_attributes": {
                        "name": record.get("scholarship_name"),
                        "provider": record.get("provider"),
                        "amount": record.get("amount"),
                        "closing_date": record.get("closing_date"),
                        "income_criteria": record.get("income_criteria"),
                        "application_url": record.get("application_url"),
                    }
                }
                
                st.json(export_data)
                
                json_bytes = json.dumps(export_data, indent=2).encode('utf-8')
                st.download_button(
                    label="📥 Download Record as JSON",
                    data=json_bytes,
                    file_name=f"scholarship_record_{db_id}.json",
                    mime="application/json",
                )

else:
    st.info("👈 Enter a URL in the sidebar control panel and click **'Execute Analysis Pipeline'** to run the crawl and verification engine.")