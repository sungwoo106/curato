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
            }
        }

        private void OnProgressUpdate(object? sender, (int progress, string message) update)
        {
            // Update progress on UI thread
            Dispatcher.Invoke(() =>
            {
                targetProgress = update.progress;
                
                // Update status message if provided
                if (!string.IsNullOrEmpty(update.message))
                {
                    LoadingTextBlock.Text = update.message;
                }
                
                // Start smooth progress animation if not already running
                if (!smoothProgressTimer.IsEnabled)
                {
                    smoothProgressTimer.Start();
                }
            });
        }

        private async void LoadingPage_LoadedAsync(object sender, EventArgs e)
        {
            Logger.LogInfo("LoadingPage_LoadedAsync - Starting");
            dotTimer.Start();
            smoothProgressTimer.Start();

            try
            {
                Logger.LogInfo("LoadingPage_LoadedAsync - Waiting for async operation");
                
                // Wait for the async operation to complete with progress tracking
                var result = await _onFinishedAsync?.Invoke();
                
                Logger.LogInfo($"LoadingPage_LoadedAsync - Async operation completed, result type: {result?.GetType().Name}");
                
                // Ensure progress reaches 100%
                targetProgress = 100;
                
                // Wait for smooth animation to complete
                await Task.Delay(500);
                
                // Stop the timers
                dotTimer.Stop();
                smoothProgressTimer.Stop();

                Logger.LogInfo("LoadingPage_LoadedAsync - Navigating to result page");

                // Navigate to the result page
                var parentWindow = Window.GetWindow(this) as MainWindow;
                if (parentWindow != null)
                {
                    parentWindow.MainFrame.Content = result ?? new OutputPage();
                    Logger.LogInfo("LoadingPage_LoadedAsync - Navigation completed");
                }
            }
            catch (Exception ex)
            {
                Logger.LogError("LoadingPage failed", ex);
                
                // Stop the timers
                dotTimer.Stop();
                smoothProgressTimer.Stop();
                
                // Navigate to search page on error
                var parentWindow = Window.GetWindow(this) as MainWindow;
                if (parentWindow != null)
                {
                    parentWindow.MainFrame.Content = new SearchPage();
                }
            }
        }
    }
}
