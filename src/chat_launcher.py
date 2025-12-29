"""Main application module for the Business Consultant Agent."""

import gradio as gr
from pathlib import Path
import markdown
import uuid
from typing import Tuple, Optional

from config import config
from services import ChatService


class BusinessConsultantAgentApp:
    """Main application class for the Business Consultant Agent."""
    
    def __init__(self):
        # Validate configuration
        if not config.validate_config():
            raise ValueError("Invalid configuration. Please check your environment variables.")
        
        self.chat_service = ChatService()
        self.current_report = None
        self.current_visualizations = []
        print(f"Business Consultant Agent application initialized for {config.name}")
    
    async def chat_handler(self, message: str, history) -> Tuple[str, Optional[str], Optional[list]]:
        """
        Handle chat messages from Gradio interface.
        Returns: (response_text, report_html, visualization_files)
        """
        try:
            response = await self.chat_service.chat(message, history)
            
            # Check if response contains a report (markdown)
            report_html = None
            visualization_files = []
            
            # Try to detect if response is a markdown report
            if response and ("#" in response or "##" in response or "###" in response):
                try:
                    # Convert markdown to HTML
                    report_html = markdown.markdown(response, extensions=['extra', 'codehilite', 'tables'])
                    self.current_report = response
                    
                    # Extract visualization paths from markdown
                    import re
                    img_pattern = r'!\[.*?\]\((.*?)\)'
                    matches = re.findall(img_pattern, response)
                    visualization_files = [m for m in matches if Path(m).exists()]
                    self.current_visualizations = visualization_files
                except Exception as e:
                    print(f"Error processing report: {e}")
            
            return response, report_html, visualization_files
        except Exception as e:
            print(f"Error in chat handler: {e}")
            error_msg = "I'm sorry, I encountered an error. Please try again."
            return error_msg, None, []
    
    def download_report_markdown(self):
        """Download current report as markdown file."""
        if not self.current_report:
            return None

        try:
            reports_dir = Path(config.reports_dir) if config and hasattr(config, 'reports_dir') else Path(__file__).resolve().parent.parent / "data" / "reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            md_path = reports_dir / f"report_{uuid.uuid4().hex[:8]}.md"
            md_path.write_text(self.current_report, encoding="utf-8")
            return str(md_path)
        except Exception as e:
            print(f"Error saving markdown: {e}")
            return None
    
    def download_report_pdf(self):
        """Download current report as PDF file."""
        if not self.current_report:
            return None
        
        try:
            from src.app_agents import export_to_pdf
            pdf_path = export_to_pdf(self.current_report)
            if pdf_path and isinstance(pdf_path, str) and Path(pdf_path).exists():
                return pdf_path
            return None
        except Exception as e:
            print(f"Error generating PDF: {e}")
            return None
    
    def create_interface(self):
        """Create enhanced Gradio interface with additional components."""
        with gr.Blocks(title="Business Consultant Agent", theme=gr.themes.Soft()) as demo:
            gr.Markdown(f"# Business Consultant Agent\n\nAsk me about your business question!")
            
            with gr.Row():
                with gr.Column(scale=2):
                    chatbot = gr.Chatbot(
                        label="Conversation",
                        height=500,
                        avatar_images=(
                            None,
                            "https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/svg/1f916.svg",
                        ),
                    )
                    msg = gr.Textbox(
                        label="Your Question",
                        placeholder="Enter your business question here...",
                        lines=2
                    )
                    submit_btn = gr.Button("Submit", variant="primary")
                    clear_btn = gr.Button("Clear")
                
                with gr.Column(scale=1):
                    with gr.Tab("Report Preview"):
                        report_html = gr.HTML(
                            label="Report Preview",
                            value="<p>Your report will appear here after analysis.</p>"
                        )
                        with gr.Row():
                            download_md = gr.File(
                                label="Download Markdown",
                                visible=False
                            )
                            download_pdf = gr.File(
                                label="Download PDF",
                                visible=False
                            )
                    
                    with gr.Tab("Visualizations"):
                        visualization_gallery = gr.Gallery(
                            label="Data Visualizations",
                            show_label=True,
                            elem_id="gallery",
                            columns=2,
                            rows=2,
                            height="auto"
                        )
                    
                    with gr.Tab("Progress"):
                        progress_text = gr.Textbox(
                            label="Status",
                            value="Ready to analyze your business question.",
                            interactive=False,
                            lines=5
                        )
            
            # Chat functionality
            async def respond(message, history):
                """Handle user message and update UI."""
                response, html, viz_files = await self.chat_handler(message, history)
                
                # Update history - Gradio 6.x uses dictionary format
                if history is None:
                    history = []
                history.append({"role": "user", "content": message})
                history.append({"role": "assistant", "content": response})

                # Update components
                updates = {
                    chatbot: gr.update(value=history),
                    msg: gr.update(value=""),
                    report_html: gr.update(value=html if html else "<p>Processing...</p>"),
                    visualization_gallery: gr.update(value=viz_files if viz_files else None),
                    progress_text: gr.update(value=f"Analysis complete. Report generated." if html else "Processing your query..."),
                }
                
                # Update download buttons
                if self.current_report:
                    md_file = self.download_report_markdown()
                    updates[download_md] = gr.update(
                        value=md_file if md_file else None,
                        visible=bool(md_file),
                        label="Download Markdown Report"
                    )
                    pdf_file = self.download_report_pdf()
                    updates[download_pdf] = gr.update(
                        value=pdf_file if pdf_file else None,
                        visible=bool(pdf_file),
                        label="Download PDF Report"
                    )
                
                return updates
            
            def clear():
                """Clear chat and reset components."""
                self.current_report = None
                self.current_visualizations = []
                return {
                    chatbot: gr.update(value=[]),
                    msg: gr.update(value=""),
                    report_html: gr.update(value="<p>Your report will appear here after analysis.</p>"),
                    visualization_gallery: gr.update(value=None),
                    progress_text: gr.update(value="Ready to analyze your business question."),
                    download_md: gr.update(visible=False),
                    download_pdf: gr.update(visible=False)
                }
            
            # Event handlers
            msg.submit(respond, [msg, chatbot], [
                chatbot, msg, report_html, visualization_gallery, progress_text, download_md, download_pdf
            ])
            submit_btn.click(respond, [msg, chatbot], [
                chatbot, msg, report_html, visualization_gallery, progress_text, download_md, download_pdf
            ])
            clear_btn.click(clear, None, [
                chatbot, msg, report_html, visualization_gallery, progress_text, download_md, download_pdf
            ])
        
        return demo
    
    def launch(self, **kwargs):
        """Launch the Gradio interface."""
        # Use enhanced interface if available, otherwise fall back to simple ChatInterface
        try:
            demo = self.create_interface()
            return demo.launch(**kwargs)
        except Exception as e:
            print(f"Error creating enhanced interface, falling back to simple interface: {e}")
            # Fallback to simple interface
            interface = gr.ChatInterface(
                self.chat_handler,
                title=f"Chat with Business Consultant Agent!",
                description=f"Ask me about your business question!"
            )
            return interface.launch(**kwargs)


def create_app() -> BusinessConsultantAgentApp:
    """Factory function to create the application."""
    return BusinessConsultantAgentApp()
