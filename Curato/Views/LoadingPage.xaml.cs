using System;
using System.Threading.Tasks;
using System.Windows.Controls;
using System.Windows.Threading;
using System.Windows;

// Currently, loading page is not synced with any specific view model.
// It serves as a temporary loading screen before navigating to the OutputPage.
// TODO: Change this to wait for actual data loading in the future.
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


        private readonly Func<UserControl>? _onFinished;

        public LoadingPage(Func<UserControl>? onFinished = null)
        {
            InitializeComponent();
            Loaded += LoadingPage_Loaded;

            _onFinished = onFinished;

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

                // Display the output page without using navigation
                var parentWindow = Window.GetWindow(this) as MainWindow;
                if (parentWindow != null)
                {
                    parentWindow.MainFrame.Content = _onFinished?.Invoke() ?? new OutputPage();
                }
            }
        }

        private void LoadingPage_Loaded(object sender, RoutedEventArgs e)
        {
            dotTimer.Start();
            progressTimer.Start();
        }
    }
}
