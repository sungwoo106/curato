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
        public double Latitude { get; set; }
        public double Longitude { get; set; }

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

            try
            {
                var htmlPath = Path.Combine(AppContext.BaseDirectory, "Resources", "html", "map_template.html");
                var kakaoMapKey = crypto_utils.get_kakao_map_api_key();

                // Build JavaScript array from AppState
                    var plan = AppState.SharedTripPlan;
                    string coordArray = "[]";
                    if (plan?.RecommendedPlaces != null)
                    {
                        var points = plan.RecommendedPlaces
                            .Where(p => p.Latitude != 0 && p.Longitude != 0)
                            .Select(p => $"{{ lat: {p.Latitude.ToString(CultureInfo.InvariantCulture)}, lng: {p.Longitude.ToString(CultureInfo.InvariantCulture)} }}");

                        coordArray = "[" + string.Join(",", points) + "]";
                    }

                    string html = File.ReadAllText(htmlPath)
                        .Replace("{API_KEY}", kakaoMapKey)
                        .Replace("{LAT}", lat.ToString(CultureInfo.InvariantCulture))
                        .Replace("{LNG}", lng.ToString(CultureInfo.InvariantCulture))
                        .Replace("{COORD_ARRAY}", coordArray);

                    await MapWebView.EnsureCoreWebView2Async();
                    MapWebView.NavigateToString(html);
                }
                catch (Exception ex)
                {
                    // optional: log the error
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


