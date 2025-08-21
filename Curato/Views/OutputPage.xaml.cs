using System.Windows;
using System.Windows.Controls;
using System.Windows.Documents;
using System.Globalization;
using System.IO;
using System.Text.Json;
using System.Text.Json.Serialization;
using Curato.Models;
using secure;
using Curato.Helpers;
using System.Text;

namespace Curato.Views
{
    public partial class OutputPage : UserControl
    {
        public double Latitude { get; set; } = 37.5665; // default to Seoul
        public double Longitude { get; set; } = 126.9780;
        private readonly StringBuilder _streamingStoryBuilder = new StringBuilder();
        private bool _isStreaming = false;

        public OutputPage()
        {
            InitializeComponent();
            this.DataContext = AppState.SharedTripPlan;
            this.Loaded += OutputPage_Loaded;

            // Set the preferences summary
            PreferencesSummaryLabel.Text = AppState.SharedInputViewModel.PreferencesSummary;
        }

        private async void OutputPage_Loaded(object sender, RoutedEventArgs e)
        {
            // Set the DataContext to the shared InputViewModel for proper data binding
            this.DataContext = AppState.SharedInputViewModel;
            
            // Set preferences summary using the ViewModel's property
            if (AppState.SharedInputViewModel != null)
            {
                var vm = AppState.SharedInputViewModel;
                // Use the existing PreferencesSummary property from the ViewModel
                PreferencesSummaryLabel.Text = vm.PreferencesSummary;
            }
            else
            {
                PreferencesSummaryLabel.Text = "Preferences not available";
            }

            // Check if we have a plan from AppState
            var plan = AppState.SharedTripPlan;

            if (plan != null && !string.IsNullOrWhiteSpace(plan.EmotionalNarrative))
            {
                // Clean the content to remove prompt instructions
                var cleanedContent = CleanStoryContent(plan.EmotionalNarrative);
                
                EmotionalItineraryTextBlock.Inlines.Clear();
                foreach (var para in cleanedContent.Split(new[] { "\n", "\r\n" }, StringSplitOptions.RemoveEmptyEntries))
                {
                    EmotionalItineraryTextBlock.Inlines.Clear();
                    EmotionalItineraryTextBlock.Inlines.Add(new Run(para.Trim()));
                    EmotionalItineraryTextBlock.Inlines.Add(new LineBreak());
                    EmotionalItineraryTextBlock.Inlines.Add(new LineBreak());
                }
            }
            else
            {
                EmotionalItineraryTextBlock.Text = "Story is being generated in real-time...";
                
                // Try to reload from AppState after a longer delay
                await Task.Delay(1000);
                var retryPlan = AppState.SharedTripPlan;
                if (retryPlan != null && !string.IsNullOrWhiteSpace(retryPlan.EmotionalNarrative))
                {
                    // Clean the content to remove prompt instructions
                    var cleanedRetryContent = CleanStoryContent(retryPlan.EmotionalNarrative);
                    
                    EmotionalItineraryTextBlock.Inlines.Clear();
                    foreach (var para in cleanedRetryContent.Split(new[] { "\n", "\r\n" }, StringSplitOptions.RemoveEmptyEntries))
                    {
                        EmotionalItineraryTextBlock.Inlines.Add(new Run(para.Trim()));
                        EmotionalItineraryTextBlock.Inlines.Add(new LineBreak());
                        EmotionalItineraryTextBlock.Inlines.Add(new LineBreak());
                    }
                }
            }

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
                var htmlPath = System.IO.Path.Combine(AppContext.BaseDirectory, "Resources", "html", "map_template.html");
                var htmlTemplate = File.ReadAllText(htmlPath, Encoding.UTF8);
                var kakaoMapKey = crypto_utils.get_kakao_map_api_key();

                // Get the plan from AppState
                var JSplan = AppState.SharedTripPlan ?? new TripPlan();
                
                                // Use the actual suggested places from the generated plan
                if (JSplan.SuggestedPlaces != null && JSplan.SuggestedPlaces.Count > 0)
                {
                    
                    
                    
                    // Find the first valid coordinate set
                    var firstValidPlace = JSplan.SuggestedPlaces.FirstOrDefault(p => 
                        p.Latitude != 0 && p.Longitude != 0 && 
                        p.Latitude >= 33.0 && p.Latitude <= 38.5 &&  // Valid Korea latitude range
                        p.Longitude >= 124.0 && p.Longitude <= 132.0 && // Valid Korea longitude range
                        // Filter out fake/placeholder coordinates
                        !(p.Latitude == 37.123456 && p.Longitude == 126.123456) &&
                        !(p.Latitude == 37.0 && p.Longitude == 126.0) &&
                        !(p.Latitude == 0.0 && p.Longitude == 0.0) &&
                        // Filter out generic placeholder names
                        !string.IsNullOrWhiteSpace(p.Name) &&
                        p.Name != "Location Name" &&
                        p.Name != "Full Address" &&
                        p.Name != "Category" &&
                        p.Name != "Distance from start" &&
                        p.Name != "Kakao Map URL"
                    );
                    
                    if (firstValidPlace != null)
                    {
                        // Use the first valid place for map center
                        lat = firstValidPlace.Latitude;
                        lng = firstValidPlace.Longitude;
                    }
                    else
                    {
                        lat = 37.5665; // Seoul
                        lng = 126.9780;
                    }
                }

                string coordArray = "[]"; // Default empty array
                
                if (JSplan.SuggestedPlaces != null && JSplan.SuggestedPlaces.Any())
                {
                    // Filter out invalid coordinates and create the array
                    var validPlaces = JSplan.SuggestedPlaces.Where(p => 
                        p.Latitude != 0 && p.Longitude != 0 && 
                        p.Latitude >= 33.0 && p.Latitude <= 38.5 &&  // Valid Korea latitude range
                        p.Longitude >= 124.0 && p.Longitude <= 132.0 && // Valid Korea longitude range
                        // Filter out fake/placeholder coordinates
                        !(p.Latitude == 37.123456 && p.Longitude == 126.123456) &&
                        !(p.Latitude == 37.0 && p.Longitude == 126.0) &&
                        !(p.Latitude == 0.0 && p.Longitude == 0.0) &&
                        // Filter out generic placeholder names
                        !string.IsNullOrWhiteSpace(p.Name) &&
                        p.Name != "Location Name" &&
                        p.Name != "Full Address" &&
                        p.Name != "Category" &&
                        p.Name != "Distance from start" &&
                        p.Name != "Kakao Map URL"
                    ).ToList();
                    
                        if (validPlaces.Any())
                        {
                            coordArray = "["
                                + string.Join(",", validPlaces
                                    .Select((p, i) =>
                                        $"{{ lat: {p.Latitude.ToString(CultureInfo.InvariantCulture)}, lng: {p.Longitude.ToString(CultureInfo.InvariantCulture)}, name: \"{p.Name.Replace("\"", "\\\"")}\", index: {i + 1} }}"))
                                + "]";
                        }



                var finalHtml = htmlTemplate
                    .Replace("{API_KEY}", kakaoMapKey)
                    .Replace("{LAT}", lat.ToString(CultureInfo.InvariantCulture))
                    .Replace("{LNG}", lng.ToString(CultureInfo.InvariantCulture))
                    .Replace("{COORD_ARRAY}", coordArray);

                await MapWebView.EnsureCoreWebView2Async();
                MapWebView.NavigateToString(finalHtml);
            }
            catch (Exception ex)
            {
                Logger.LogError($"Failed to load map: {ex.Message}", ex);
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

        private void ViewLogButton_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                var logContents = Logger.GetLogContents();
                var logWindow = new Window
                {
                    Title = "Curato Debug Log",
                    Width = 800,
                    Height = 600,
                    WindowStartupLocation = WindowStartupLocation.CenterScreen,
                    ResizeMode = ResizeMode.CanResize
                };

                var textBox = new TextBox
                {
                    Text = logContents,
                    IsReadOnly = true,
                    VerticalScrollBarVisibility = ScrollBarVisibility.Auto,
                    HorizontalScrollBarVisibility = ScrollBarVisibility.Auto,
                    FontFamily = new System.Windows.Media.FontFamily("Consolas"),
                    FontSize = 12
                };

                var clearButton = new Button
                {
                    Content = "Clear Log",
                    Width = 100,
                    Height = 30,
                    Margin = new Thickness(10),
                    HorizontalAlignment = HorizontalAlignment.Right
                };

                clearButton.Click += (s, args) =>
                {
                    Logger.ClearLog();
                    textBox.Text = "Log cleared.";
                };

                var buttonPanel = new StackPanel
                {
                    Orientation = Orientation.Horizontal,
                    HorizontalAlignment = HorizontalAlignment.Right,
                    Margin = new Thickness(10)
                };
                buttonPanel.Children.Add(clearButton);

                var mainPanel = new DockPanel();
                DockPanel.SetDock(buttonPanel, Dock.Top);
                mainPanel.Children.Add(buttonPanel);
                mainPanel.Children.Add(textBox);

                logWindow.Content = mainPanel;
                logWindow.Show();
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Failed to show log: {ex.Message}", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        /// <summary>
        /// Cleans the story content by removing prompt instructions and technical markers
        /// </summary>
        /// <param name="rawContent">Raw content from the AI model</param>
        /// <returns>Cleaned content suitable for display</returns>
        private string CleanStoryContent(string rawContent)
        {
            if (string.IsNullOrWhiteSpace(rawContent))
                return rawContent;

            var lines = rawContent.Split(new[] { "\n", "\r\n" }, StringSplitOptions.RemoveEmptyEntries);
            var cleanedLines = new List<string>();

            foreach (var line in lines)
            {
                var trimmedLine = line.Trim();
                
                // Skip lines that contain prompt instructions
                if (trimmedLine.StartsWith("You are a professional travel writer") ||
                    trimmedLine.StartsWith("Create a comprehensive itinerary") ||
                    trimmedLine.StartsWith("IMPORTANT:") ||
                    trimmedLine.StartsWith("Context:") ||
                    trimmedLine.StartsWith("Requirements:") ||
                    trimmedLine.StartsWith("Output Format:") ||
                    trimmedLine.StartsWith("Selected Locations:") ||
                    trimmedLine.StartsWith("I'll create a comprehensive itinerary") ||
                    trimmedLine.StartsWith("I have now covered all") ||
                    trimmedLine.StartsWith("[BEGIN]:") ||
                    trimmedLine.StartsWith("[END]") ||
                    trimmedLine.StartsWith("1.") && trimmedLine.Contains("Place Name") ||
                    trimmedLine.StartsWith("2.") && trimmedLine.Contains("Place Name") ||
                    trimmedLine.StartsWith("3.") && trimmedLine.Contains("Place Name") ||
                    trimmedLine.StartsWith("4.") && trimmedLine.Contains("Place Name") ||
                    trimmedLine.StartsWith("5.") && trimmedLine.Contains("Place Name"))
                {
                    continue; // Skip this line
                }

                // Skip empty lines and technical markers
                if (string.IsNullOrWhiteSpace(trimmedLine) || 
                    trimmedLine.StartsWith("\\") ||
                    trimmedLine.StartsWith("Continue this format"))
                {
                    continue;
                }

                cleanedLines.Add(trimmedLine);
            }

            return string.Join("\n", cleanedLines);
        }

        /// <summary>
        /// Receives streaming tokens for real-time story display
        /// </summary>
        /// <param name="token">The token to display</param>
        /// <param name="isFinal">Whether this is the final token</param>
        public void ReceiveStreamingToken(string token, bool isFinal = false)
        {
            try
            {
                if (isFinal)
                {
                    // Final token received - story generation complete
                    _isStreaming = false;
                    Logger.LogInfo("Streaming completed - story generation finished");
                    
                    // Update the final story in AppState if we have a complete story
                    if (_streamingStoryBuilder.Length > 0)
                    {
                        var finalStory = _streamingStoryBuilder.ToString();
                        if (AppState.SharedTripPlan != null)
                        {
                            AppState.SharedTripPlan.EmotionalNarrative = finalStory;
                        }
                        Logger.LogInfo($"Final streaming story saved to AppState: {finalStory.Substring(0, Math.Min(100, finalStory.Length))}...");
                    }
                    return;
                }
                
                if (string.IsNullOrEmpty(token))
                    return;
                
                // Start streaming mode if not already started
                if (!_isStreaming)
                {
                    _isStreaming = true;
                    _streamingStoryBuilder.Clear();
                    EmotionalItineraryTextBlock.Inlines.Clear();
                    Logger.LogInfo("Starting real-time story streaming");
                }
                
                // Add token to builder
                _streamingStoryBuilder.Append(token);
                
                // Display token in real-time
                Dispatcher.Invoke(() =>
                {
                    EmotionalItineraryTextBlock.Inlines.Add(new Run(token));
                    
                    // Auto-scroll to bottom
                    var scrollViewer = FindScrollViewer();
                    if (scrollViewer != null)
                    {
                        scrollViewer.ScrollToBottom();
                    }
                });
                
            }
            catch (Exception ex)
            {
                Logger.LogError($"Error processing streaming token: {ex.Message}", ex);
            }
        }
        
        /// <summary>
        /// Finds the ScrollViewer parent of the EmotionalItineraryTextBlock
        /// </summary>
        private ScrollViewer? FindScrollViewer()
        {
            var parent = EmotionalItineraryTextBlock.Parent as FrameworkElement;
            while (parent != null)
            {
                if (parent is ScrollViewer scrollViewer)
                    return scrollViewer;
                parent = parent.Parent as FrameworkElement;
            }
            return null;
        }
    }
}


