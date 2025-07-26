using System.Windows;
using System.Windows.Controls;
using System.Windows.Documents;
using System.Globalization;
using System.IO;
using secure;

namespace Curato.Views
{
    public partial class OutputPage : UserControl
    {
        public OutputPage()
        {
            InitializeComponent();
            this.DataContext = AppState.SharedTripPlan;

            this.Loaded += OutputPage_Loaded;

            // Load the emotional narrative into the TextBlock
            var plan = AppState.SharedTripPlan;

            // Set the preferences summary
            PreferencesSummaryLabel.Text = AppState.SharedInputViewModel.PreferencesSummary;

            if (plan != null && !string.IsNullOrWhiteSpace(plan.EmotionalNarrative))
            {
                EmotionalItineraryTextBlock.Inlines.Clear();
                foreach (var para in plan.EmotionalNarrative.Split(new[] { "\n", "\r\n" }, StringSplitOptions.RemoveEmptyEntries))
                {
                    EmotionalItineraryTextBlock.Inlines.Add(new Run(para.Trim()));
                    EmotionalItineraryTextBlock.Inlines.Add(new LineBreak());
                    EmotionalItineraryTextBlock.Inlines.Add(new LineBreak());
                }
            }
        }

        private async void OutputPage_Loaded(object sender, RoutedEventArgs e)
        {
            // Debugging
            string logPath = Path.Combine(AppContext.BaseDirectory, "map_debug_log.txt");
            void Log(string msg) => File.AppendAllText(logPath, $"[{DateTime.Now:yyyy-MM-dd HH:mm:ss}] {msg}\n");
            Log("=== OutputPage_Loaded triggered ===");

            double lat = 37.5665; // default to Seoul
            double lng = 126.9780;

            var coords = AppState.SharedInputViewModel.SelectedLocationCoordinates;
            if (coords.HasValue)
            {
                lat = coords.Value.Latitude;
                lng = coords.Value.Longitude;
                // Debugging
                Log($"Coordinates received: lat={lat}, lng={lng}");
            }
            // Debuggng
            else
            {
                Log("⚠️ No coordinates provided, using default (Seoul)");
            }

            try
            {
                var htmlPath = Path.Combine(AppContext.BaseDirectory, "Resources", "html", "map_template.html");
                // Debugging
                Log($"Checking HTML path: {htmlPath}");

                // Debugging
                if (!File.Exists(htmlPath))
                {
                    Log(" map_template.html NOT found!");
                    return;
                }
                Log(" map_template.html found");

                var kakaoMapKey = crypto_utils.get_kakao_map_api_key();

                // Debugging
                Log($" Kakao API Key (length): {kakaoMapKey?.Length}");

                string html = File.ReadAllText(htmlPath)
                    .Replace("{API_KEY}", kakaoMapKey)
                    .Replace("{LAT}", lat.ToString(CultureInfo.InvariantCulture))
                    .Replace("{LNG}", lng.ToString(CultureInfo.InvariantCulture));

                // Debugging
                string debugHtmlPath = Path.Combine(AppContext.BaseDirectory, "debug_map_rendered.html");
                File.WriteAllText(debugHtmlPath, html);
                Log($" HTML output written to: {debugHtmlPath}");

                await MapWebView.EnsureCoreWebView2Async();

                // Debugging
                MapWebView.NavigationCompleted += (s, args) =>
                {
                    if (args.IsSuccess)
                        Log(" WebView2 loaded HTML successfully.");
                    else
                        Log($" WebView2 failed to load HTML: {args.WebErrorStatus}");
                };
                MapWebView.CoreWebView2InitializationCompleted += (s, args) =>
                {
                    if (args.IsSuccess)
                        Log(" WebView2 CoreWebView2 initialized.");
                    else
                        Log($" CoreWebView2 init failed: {args.InitializationException?.Message}");
                };

                MapWebView.NavigateToString(html);

                //Debugging
                Log("🚀 Sent HTML to WebView2.");
                
            }
            catch
            {
                // ignore map errors

                //Debugging
                Log("❌ Exception in OutputPage_Loaded: " + ex);
            }
        }

        private void EditButton_Click(object sender, RoutedEventArgs e)
        {
            var mainWindow = Window.GetWindow(this) as MainWindow;
            if (mainWindow != null)
            {
                mainWindow.MainFrame.Content = new SearchPage();
            }
        }
    }
}


