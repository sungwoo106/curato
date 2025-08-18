using System;
using System.Threading.Tasks;
using System.Windows.Controls;
using System.Windows.Threading;
using System.Windows;

namespace Curato.Views
{
    public partial class LoadingPage : UserControl
    {
        private readonly DispatcherTimer dotTimer;
        private readonly DispatcherTimer progressTimer;
        private int dotCount = 0;
        private readonly string baseText = "Planning your trip";
        private double MaxBarWidth = 800;
        private double progress = 0;

        private readonly Func<Task<UserControl>>? _onFinishedAsync;
        private readonly Func<UserControl>? _onFinished;

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

            progressTimer = new DispatcherTimer
            {
                Interval = TimeSpan.FromMilliseconds(30)
            };
            progressTimer.Tick += ProgressTimer_Tick;
        }

        public LoadingPage(Func<UserControl> onFinished) : this(() => Task.FromResult(onFinished()))
        {
            _onFinished = onFinished;
        }

        private void DotTimer_Tick(object sender, EventArgs e)
        {
            dotCount = (dotCount + 1) % 4;
            LoadingTextBlock.Text = baseText + new string('.', dotCount);
        }

        private void ProgressTimer_Tick(object sender, EventArgs e)
        {
            progress += 1;
            ProgressBarFill.Width = progress / 100 * MaxBarWidth;

            if (progress >= 100)
            {
                dotTimer.Stop();
                progressTimer.Stop();
            }
        }

        private async void LoadingPage_LoadedAsync(object sender, EventArgs e)
        {
            Logger.LogInfo("LoadingPage_LoadedAsync - Starting");
            dotTimer.Start();
            progressTimer.Start();

            try
            {
                Logger.LogInfo("LoadingPage_LoadedAsync - Waiting for async operation");
                
                // Wait for the async operation to complete
                var result = await _onFinishedAsync?.Invoke();
                
                Logger.LogInfo($"LoadingPage_LoadedAsync - Async operation completed, result type: {result?.GetType().Name}");
                
                // Stop the timers
                dotTimer.Stop();
                progressTimer.Stop();

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
                progressTimer.Stop();
                
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
