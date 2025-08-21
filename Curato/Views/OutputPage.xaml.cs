using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Controls.Primitives;
using System.Windows.Documents;

using System.Windows.Media;
using System.Windows.Threading;
using System.Globalization;
using System.IO;
using System.Text.Json;
using System.Text.Json.Serialization;
using Curato;
using Curato.Models;
using Curato.Views;
using Microsoft.Web.WebView2.Wpf;
using secure;
using Curato.Helpers;
using System.Text;

namespace Curato.Views
{
    public partial class OutputPage : UserControl
    {
        private readonly StringBuilder _streamingStoryBuilder = new StringBuilder();
        private bool _isStreaming = false;
        private DateTime _streamingStartTime;
        private const int BEGIN_MARKER_TIMEOUT_SECONDS = 30; // 30 seconds timeout for [BEGIN] marker
        
        // Properties for map coordinates (used by Kakao Map API)
        public double Latitude { get; set; } = 37.5665; // Default to Seoul
        public double Longitude { get; set; } = 126.9780; // Default to Seoul

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
                // Display the content directly (Qwen output is already clean)
                EmotionalItineraryTextBlock.Inlines.Clear();
                foreach (var para in plan.EmotionalNarrative.Split(new[] { "\n", "\r\n" }, StringSplitOptions.RemoveEmptyEntries))
                {
                    EmotionalItineraryTextBlock.Inlines.Add(new Run(para.Trim()));
                    EmotionalItineraryTextBlock.Inlines.Add(new LineBreak());
                    EmotionalItineraryTextBlock.Inlines.Add(new LineBreak());
                }
            }
            else
            {
                EmotionalItineraryTextBlock.Text = "Story is being generated in real-time...\n\n";
                
                // Try to reload from AppState after a longer delay
                await Task.Delay(1000);
                var retryPlan = AppState.SharedTripPlan;
                if (retryPlan != null && !string.IsNullOrWhiteSpace(retryPlan.EmotionalNarrative))
                {
                    // Display the content directly (Qwen output is already clean)
                    EmotionalItineraryTextBlock.Inlines.Clear();
                    foreach (var para in retryPlan.EmotionalNarrative.Split(new[] { "\n", "\r\n" }, StringSplitOptions.RemoveEmptyEntries))
                    {
                        EmotionalItineraryTextBlock.Inlines.Add(new Run(para.Trim()));
                        EmotionalItineraryTextBlock.Inlines.Add(new LineBreak());
                        EmotionalItineraryTextBlock.Inlines.Add(new LineBreak());
                    }
                }
            }

            double lat = 37.5665; // default to Seoul
            double lng = 126.9780;

            var coords = AppState.SharedInputViewModel?.SelectedLocationCoordinates;
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
        /// Receives streaming tokens for real-time story display with frontend filtering
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
                    
                    // Log the complete story for debugging
                    var completeStory = _streamingStoryBuilder.ToString();
                    Logger.LogInfo($"Complete story received: {completeStory.Substring(0, Math.Min(200, completeStory.Length))}...");
                    
                    // Save the complete story to AppState (real-time filtering already handled display)
                    if (!string.IsNullOrWhiteSpace(completeStory))
                    {
                        if (AppState.SharedTripPlan != null)
                        {
                            AppState.SharedTripPlan.EmotionalNarrative = completeStory;
                        }
                        Logger.LogInfo($"Complete story saved to AppState: {completeStory.Substring(0, Math.Min(100, completeStory.Length))}...");
                    }
                    return;
                }
                
                if (string.IsNullOrEmpty(token))
                    return;
                
                // Start streaming mode if not already started
                if (!_isStreaming)
                {
                    _isStreaming = true;
                    _streamingStartTime = DateTime.Now;
                    _streamingStoryBuilder.Clear();
                    EmotionalItineraryTextBlock.Inlines.Clear();
                    
                    // Show loading message while waiting for [BEGIN] marker
                    EmotionalItineraryTextBlock.Inlines.Add(new Run("Generating your personalized itinerary..."));
                    EmotionalItineraryTextBlock.Inlines.Add(new LineBreak());
                    EmotionalItineraryTextBlock.Inlines.Add(new LineBreak());
                    
                    Logger.LogInfo("Starting real-time story streaming with frontend filtering");
                }
                
                // Check for timeout if we haven't found [BEGIN] marker yet
                var fullContent = _streamingStoryBuilder.ToString();
                if (!fullContent.Contains("[BEGIN]: "))
                {
                    var elapsedSeconds = (DateTime.Now - _streamingStartTime).TotalSeconds;
                    if (elapsedSeconds > BEGIN_MARKER_TIMEOUT_SECONDS)
                    {
                        // Show a warning message
                        Dispatcher.Invoke(() =>
                        {
                            EmotionalItineraryTextBlock.Inlines.Clear();
                            EmotionalItineraryTextBlock.Inlines.Add(new Run("Warning: [BEGIN] marker not found. Displaying all content."));
                            EmotionalItineraryTextBlock.Inlines.Add(new LineBreak());
                            EmotionalItineraryTextBlock.Inlines.Add(new LineBreak());
                        });
                    }
                }
                
                // Add token to builder for complete story tracking
                _streamingStoryBuilder.Append(token);

                // Real-time frontend filtering: only show content after [BEGIN] marker
                var filteredToken = FilterTokenForDisplay(token);
                
                if (!string.IsNullOrEmpty(filteredToken))
                {
                    // Display filtered token in real-time
                    Dispatcher.Invoke(() =>
                    {
                        EmotionalItineraryTextBlock.Inlines.Add(new Run(filteredToken));
                        
                        // Auto-scroll to bottom
                        var scrollViewer = FindScrollViewer();
                        if (scrollViewer != null)
                        {
                            scrollViewer.ScrollToBottom();
                        }
                    });
                }
            }
            catch (Exception ex)
            {
                Logger.LogError($"Error processing streaming token: {ex.Message}", ex);
            }
        }
        
        /// <summary>
        /// Filters tokens to only show content after [BEGIN] marker
        /// </summary>
        /// <param name="token">The raw token to filter</param>
        /// <returns>Filtered token content, or empty string if should not be displayed</returns>
        private string FilterTokenForDisplay(string token)
        {
            // Get the current state from the full content
            var fullContent = _streamingStoryBuilder.ToString();
            var hasBegin = fullContent.Contains("[BEGIN]: ");
            
            // Check if this token contains the [BEGIN] marker
            if (token.Contains("[BEGIN]: "))
            {
                ClearLoadingMessage();
                // Extract content after [BEGIN] marker if any
                var beginIndex = token.IndexOf("[BEGIN]: ");
                if (beginIndex >= 0)
                {
                    var contentAfterBegin = token.Substring(beginIndex + "[BEGIN]: ".Length);
                    return !string.IsNullOrWhiteSpace(contentAfterBegin) ? contentAfterBegin : string.Empty;
                }
                return string.Empty; // Don't show the [BEGIN] marker itself
            }
            
            // Only show content if we've found the [BEGIN] marker
            if (hasBegin)
            {
                return token;
            }
            
            // Don't show content before [BEGIN]
            return string.Empty;
        }
        
        /// <summary>
        /// Clears the loading message when [BEGIN] marker is found
        /// </summary>
        private void ClearLoadingMessage()
        {
            Dispatcher.Invoke(() =>
            {
                EmotionalItineraryTextBlock.Inlines.Clear();
            });
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