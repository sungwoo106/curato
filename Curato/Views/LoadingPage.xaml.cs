using System;
using System.Threading.Tasks;
using System.Windows.Controls;
using System.Windows.Threading;
using System.Windows;
using Curato.Helpers;
using System.ComponentModel;

namespace Curato.Views
{
    public partial class LoadingPage : UserControl
    {
        private readonly DispatcherTimer dotTimer;
        private readonly DispatcherTimer smoothProgressTimer;
        private int dotCount = 0;
        private readonly string baseText = "Planning your trip";
        private double MaxBarWidth = 800;
        private double currentProgress = 0;
        private double targetProgress = 0;
        private double smoothProgress = 0;

        private readonly Func<Task<UserControl>>? _onFinishedAsync;
        private readonly Func<UserControl>? _onFinished;
        private Progress<(int progress, string message)>? _progressTracker;
        private MainWindow? _parentWindow;
        private bool _phiCompleted = false;
        private bool _streamingStarted = false;
        private OutputPage? _currentOutputPage;
        private string? _routePlanData; // Store route plan data for early output page

        public LoadingPage(Func<Task<UserControl>> onFinishedAsync)
        {
            InitializeComponent();
            Loaded += LoadingPage_LoadedAsync;

            _onFinishedAsync = onFinishedAsync;

            dotTimer = new DispatcherTimer
            {
                Interval = TimeSpan.FromMilliseconds(500)
            };
            dotTimer.Tick += DotTimer_Tick;

            smoothProgressTimer = new DispatcherTimer
            {
                Interval = TimeSpan.FromMilliseconds(16) // 60 FPS for smooth animation
            };
            smoothProgressTimer.Tick += SmoothProgressTimer_Tick;
        }

        public LoadingPage(Func<UserControl> onFinished) : this(() => Task.FromResult(onFinished()))
        {
            _onFinished = onFinished;
        }

        public void SetProgressTracker(Progress<(int progress, string message)> progressTracker)
        {
            _progressTracker = progressTracker;
            _progressTracker.ProgressChanged += OnProgressUpdate;
        }

        private void DotTimer_Tick(object sender, EventArgs e)
        {
            dotCount = (dotCount + 1) % 4;
            LoadingTextBlock.Text = baseText + new string('.', dotCount);
        }

        private void SmoothProgressTimer_Tick(object sender, EventArgs e)
        {
            // Smooth interpolation between current and target progress
            if (Math.Abs(smoothProgress - targetProgress) > 0.5)
            {
                smoothProgress += (targetProgress - smoothProgress) * 0.1; // Smooth easing
                currentProgress = smoothProgress;
                ProgressBarFill.Width = (currentProgress / 100) * MaxBarWidth;
                
                // Update progress percentage text
                ProgressPercentageText.Text = $"{Math.Round(currentProgress)}%";
            }
            else if (targetProgress >= 100)
            {
                // Animation complete
                smoothProgressTimer.Stop();
                dotTimer.Stop();
                
                // Ensure final values are set
                currentProgress = 100;
                ProgressBarFill.Width = MaxBarWidth;
                ProgressPercentageText.Text = "100%";
                
                // Show completion message in subtext
                ProgressSubtext.Text = "Trip planning completed!";
            }
        }

        private void OnProgressUpdate(object? sender, (int progress, string message) update)
        {
            // Update progress on UI thread
            Dispatcher.Invoke(() =>
            {
                targetProgress = update.progress;
                
                // Handle special streaming messages
                if (update.message.StartsWith("streaming_token:"))
                {
                    // This is a streaming token - handle it specially
                    if (!_streamingStarted)
                    {
                        _streamingStarted = true;
                        ProgressSubtext.Text = "Generating story in real-time...";
                    }
                    
                    // Extract the token and send it to the OutputPage
                    var token = update.message.Substring("streaming_token:".Length);
                    if (_currentOutputPage != null)
                    {
                        _currentOutputPage.ReceiveStreamingToken(token, false);
                    }
                    
                    return; // Don't update subtext for streaming tokens
                }
                
                // Update status message in subtext if provided
                if (!string.IsNullOrEmpty(update.message))
                {
                    ProgressSubtext.Text = update.message;
                }
                
                // Check if Phi has completed and we should show output page
                if (update.message.StartsWith("phi_completion:") && !_phiCompleted)
                {
                    _phiCompleted = true;
                    
                    // Extract the route plan data from the message
                    var routePlanData = update.message.Substring("phi_completion:".Length);
                    if (!string.IsNullOrEmpty(routePlanData))
                    {
                        _routePlanData = routePlanData;
                        Logger.LogInfo($"LoadingPage - Extracted route plan data: {routePlanData.Substring(0, Math.Min(100, routePlanData.Length))}...");
                    }
                    
                    ProgressSubtext.Text = "Phi model completed - showing output page";
                    
                    // Show output page immediately after Phi completes
                    ShowOutputPageEarly();
                }
                
                // Check if story streaming completed
                if (update.message.Contains("Story streaming completed"))
                {
                    // Send final token to OutputPage
                    if (_currentOutputPage != null)
                    {
                        _currentOutputPage.ReceiveStreamingToken("", true);
                    }
                }
                
                // Start smooth progress animation if not already running
                if (!smoothProgressTimer.IsEnabled)
                {
                    smoothProgressTimer.Start();
                }
            });
        }
        
        private async void ShowOutputPageEarly()
        {
            try
            {
                Logger.LogInfo("LoadingPage - Phi completed, showing output page early");
                
                // Parse the route plan data and populate AppState before showing OutputPage
                if (!string.IsNullOrEmpty(_routePlanData))
                {
                    try
                    {
                        // Parse the route plan JSON and create a TripPlan object
                        var routePlan = System.Text.Json.JsonSerializer.Deserialize<Curato.Models.TripPlan>(_routePlanData);
                        if (routePlan != null)
                        {
                            // Set the route plan in AppState so the map can access it
                            AppState.SharedTripPlan = routePlan;
                            Logger.LogInfo($"LoadingPage - Route plan parsed and set in AppState: {routePlan.SuggestedPlaces?.Count ?? 0} places");
                        }
                    }
                    catch (Exception ex)
                    {
                        Logger.LogError($"Failed to parse route plan data: {ex.Message}", ex);
                    }
                }
                
                // Create a basic OutputPage to show immediately
                _currentOutputPage = new OutputPage();
                
                // Get the parent window
                if (_parentWindow == null)
                {
                    _parentWindow = Window.GetWindow(this) as MainWindow;
                }
                
                if (_parentWindow != null)
                {
                    // Show the output page immediately
                    _parentWindow.MainFrame.Content = _currentOutputPage;
                    
                    // Continue monitoring progress for story streaming
                    // The story will be streamed to the OutputPage in real-time
                    Logger.LogInfo("LoadingPage - Output page shown, continuing to monitor story streaming");
                }
            }
            catch (Exception ex)
            {
                Logger.LogError("Failed to show output page early", ex);
            }
        }

        private async void LoadingPage_LoadedAsync(object sender, EventArgs e)
        {
            Logger.LogInfo("LoadingPage_LoadedAsync - Starting");
            dotTimer.Start();
            smoothProgressTimer.Start();

            // Set initial subtext message
            ProgressSubtext.Text = "Preparing your personalized trip...";
            
            // Get reference to parent window
            _parentWindow = Window.GetWindow(this) as MainWindow;

            try
            {
                Logger.LogInfo("LoadingPage_LoadedAsync - Waiting for async operation");
                
                // Wait for the async operation to complete with progress tracking
                var result = await _onFinishedAsync?.Invoke();
                
                Logger.LogInfo($"LoadingPage_LoadedAsync - Async operation completed, result type: {result?.GetType().Name}");
                
                // If we haven't shown the output page yet (Phi didn't complete), show it now
                if (!_phiCompleted)
                {
                    // Ensure progress reaches 100%
                    targetProgress = 100;
                    
                    // Wait for smooth animation to complete
                    await Task.Delay(500);
                    
                    // Stop the timers
                    dotTimer.Stop();
                    smoothProgressTimer.Stop();

                    Logger.LogInfo("LoadingPage_LoadedAsync - Navigating to result page");

                    // Navigate to the result page
                    if (_parentWindow != null)
                    {
                        _parentWindow.MainFrame.Content = result ?? new OutputPage();
                        Logger.LogInfo("LoadingPage_LoadedAsync - Navigation completed");
                    }
                }
                else
                {
                    // Phi already completed and output page is shown
                    // Just ensure the final result is properly set
                    Logger.LogInfo("LoadingPage_LoadedAsync - Phi already completed, output page already shown");
                    
                    // Stop the timers
                    dotTimer.Stop();
                    smoothProgressTimer.Stop();
                }
            }
            catch (Exception ex)
            {
                Logger.LogError("LoadingPage failed", ex);
                
                // Stop the timers
                dotTimer.Stop();
                smoothProgressTimer.Stop();
                
                // Navigate to search page on error
                if (_parentWindow != null)
                {
                    _parentWindow.MainFrame.Content = new SearchPage();
                }
            }
        }
    }
}
