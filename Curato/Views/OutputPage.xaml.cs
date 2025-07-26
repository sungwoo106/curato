using System.Windows;
using System.Windows.Controls;
using System.Windows.Documents;
using System.Globalization;
using System.IO;

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
            double lat = 37.5665; // default to Seoul
            double lng = 126.9780;

            var coords = AppState.SharedInputViewModel.SelectedLocationCoordinates;
            if (coords.HasValue)
            {
                lat = coords.Value.Latitude;
                lng = coords.Value.Longitude;
            }

            string apiKey = Environment.GetEnvironmentVariable("KAKAO_MAP_API_KEY") ?? "";

            try
            {
                var htmlPath = Path.Combine(AppContext.BaseDirectory, "Resources", "Html", "map_template.html");
                if (File.Exists(htmlPath))
                {
                    string html = File.ReadAllText(htmlPath)
                        .Replace("{{API_KEY}}", apiKey)
                        .Replace("{{LAT}}", lat.ToString(CultureInfo.InvariantCulture))
                        .Replace("{{LNG}}", lng.ToString(CultureInfo.InvariantCulture));

                    await MapWebView.EnsureCoreWebView2Async();
                    MapWebView.NavigateToString(html);
                }
            }
            catch
            {
                // ignore map errors
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


